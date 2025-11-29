"""
Simplified FHIR Pipeline - LLM-driven with standardized codes from CSV.
Send any medical data → LLM matches to standardized code → generates FHIR JSON.
"""

import csv
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from openai import OpenAI

# ============ CONFIG ============
FHIR_BASE = "http://localhost:32783/csp/healthshare/demo/fhir/r4"
FHIR_AUTH = ("_SYSTEM", "ISCDEMO")
FHIR_HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}
CODES_CSV = Path(__file__).parent / "fhir_codes.csv"
CODE_SYSTEM = "https://hackbrno.vercel.app/fhir/codes"


@dataclass
class CodeMatch:
    """Result of code matching."""
    code: str
    description: str
    resource_type: str
    category: str
    confidence: float = 1.0


@dataclass
class IngestResult:
    """Result of ingestion."""
    success: bool
    resource_type: str
    fhir_json: Dict
    matched_code: Optional[CodeMatch] = None
    server_response: Optional[Dict] = None
    error: Optional[str] = None


def load_codes(csv_path: Path = CODES_CSV) -> List[Dict]:
    """Load standardized codes from CSV."""
    codes = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            codes.append(row)
    return codes


class SimpleFHIRPipeline:
    """Send ANY medical data - LLM matches to code, then generates FHIR structure."""
    
    MATCH_PROMPT = """You are a medical coding expert. Given a field name and value, match it to the BEST code from the list.

AVAILABLE CODES:
{codes_list}

INPUT:
- Field: {field_name}
- Value: {value}

OUTPUT JSON:
{{"code": "<CODE>", "confidence": 0.0-1.0}}

Pick the SINGLE best matching code. If nothing matches well, use confidence < 0.5.
Output ONLY JSON."""

    GENERATE_PROMPT = """You are a FHIR expert. Generate a FHIR {resource_type} resource.

RULES:
1. Use the provided standardized code in the "code" field with coding array
2. Include: resourceType, status, subject reference, date field
3. Keep it minimal

INPUT:
- Patient ID: {patient_id}
- Code: {code} (system: {system})
- Description: {description}
- Value: {value}
- Date: {date}

STRUCTURE for code field:
"code": {{
  "coding": [{{"system": "{system}", "code": "{code}", "display": "{description}"}}],
  "text": "{description}"
}}

For Observation: use valueString or valueQuantity, effectiveDateTime
For Condition: use onsetDateTime, clinicalStatus
For Procedure: use performedDateTime, status

Output ONLY valid JSON."""

    def __init__(self, openai_client: Optional[OpenAI] = None, codes_csv: Path = CODES_CSV):
        self.client = openai_client or OpenAI()
        self.codes = load_codes(codes_csv)
        self._codes_list_str = "\n".join(
            f"- {c['code']}: {c['description']} ({c['resource_type']})" 
            for c in self.codes
        )
    
    def ingest(
        self, 
        patient_id: str, 
        field_name: str, 
        value: str, 
        date: str,
        send_to_server: bool = True
    ) -> IngestResult:
        """Ingest a single medical field into FHIR."""
        
        # Step 1: Match field to standardized code
        matched = self._match_code(field_name, value)
        
        if not matched or matched.confidence < 0.3:
            return IngestResult(
                False, "unknown", {}, matched,
                error=f"No matching code found (confidence: {matched.confidence if matched else 0})"
            )
        
        # Step 2: Generate FHIR JSON using matched code
        fhir_json = self._generate_fhir(patient_id, matched, value, date)
        
        if not fhir_json:
            return IngestResult(False, matched.resource_type, {}, matched, error="Failed to generate FHIR JSON")
        
        resource_type = fhir_json.get("resourceType", matched.resource_type)
        
        # Step 3: Send to server (optional)
        server_response = None
        if send_to_server:
            server_response = self._send(fhir_json)
            success = server_response.get("success", False)
        else:
            success = True
        
        return IngestResult(success, resource_type, fhir_json, matched, server_response)
    
    def ingest_batch(
        self,
        patient_id: str,
        data: Dict[str, tuple],  # {"field": (date, value), ...}
        send_to_server: bool = True
    ) -> List[IngestResult]:
        """Ingest multiple fields for a patient."""
        results = []
        
        # Always create patient first
        patient_json = {"resourceType": "Patient", "id": patient_id}
        if send_to_server:
            self._send(patient_json)
        
        for field_name, (date, value) in data.items():
            result = self.ingest(patient_id, field_name, value, date, send_to_server)
            results.append(result)
        
        return results
    
    def _match_code(self, field_name: str, value: str) -> Optional[CodeMatch]:
        """Use LLM to match field to standardized code."""
        
        prompt = self.MATCH_PROMPT.format(
            codes_list=self._codes_list_str,
            field_name=field_name,
            value=value
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            code = result.get("code")
            confidence = result.get("confidence", 0.5)
            
            # Find code details
            code_info = next((c for c in self.codes if c["code"] == code), None)
            if code_info:
                return CodeMatch(
                    code=code,
                    description=code_info["description"],
                    resource_type=code_info["resource_type"],
                    category=code_info["category"],
                    confidence=confidence
                )
            return None
            
        except Exception as e:
            print(f"Code matching error: {e}")
            return None
    
    def _generate_fhir(self, patient_id: str, matched: CodeMatch, value: str, date: str) -> Optional[Dict]:
        """Generate FHIR JSON using matched code."""
        
        prompt = self.GENERATE_PROMPT.format(
            resource_type=matched.resource_type,
            patient_id=patient_id,
            code=matched.code,
            system=CODE_SYSTEM,
            description=matched.description,
            value=value,
            date=date
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"FHIR generation error: {e}")
            return None
    
    def _send(self, resource: Dict) -> Dict:
        """Send resource to FHIR server."""
        resource_type = resource["resourceType"]
        resource_id = resource.get("id")
        
        if resource_id:
            url = f"{FHIR_BASE}/{resource_type}/{resource_id}"
            method = "PUT"
        else:
            url = f"{FHIR_BASE}/{resource_type}"
            method = "POST"
        
        try:
            response = requests.request(method, url, json=resource, headers=FHIR_HEADERS, auth=FHIR_AUTH)
            return {
                "success": response.status_code in (200, 201),
                "status": response.status_code,
                "response": response.json() if response.text else {}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_codes(self) -> List[Dict]:
        """List all available codes."""
        return self.codes
    
    def ensure_patient(self, patient_id: str) -> Dict:
        """
        Create patient if it doesn't exist, otherwise return existing.
        Returns: {"exists": bool, "created": bool, "patient": dict}
        """
        # Check if patient exists
        check_url = f"{FHIR_BASE}/Patient/{patient_id}"
        try:
            response = requests.get(check_url, headers=FHIR_HEADERS, auth=FHIR_AUTH)
            
            if response.status_code == 200:
                # Patient exists
                return {
                    "exists": True,
                    "created": False,
                    "patient": response.json()
                }
            
            # Patient doesn't exist, create it
            patient_resource = {
                "resourceType": "Patient",
                "id": patient_id,
                "identifier": [{
                    "system": CODE_SYSTEM,
                    "value": patient_id
                }]
            }
            
            create_result = self._send(patient_resource)
            
            return {
                "exists": False,
                "created": create_result["success"],
                "patient": patient_resource,
                "server_response": create_result
            }
            
        except Exception as e:
            return {"exists": False, "created": False, "error": str(e)}
    
    def get_patient_data(self, patient_id: str) -> Dict:
        """
        Get all FHIR data for a patient.
        Returns structured summary with all resources.
        """
        # Use $everything operation to get all related resources
        url = f"{FHIR_BASE}/Patient/{patient_id}/$everything"
        
        try:
            response = requests.get(url, headers=FHIR_HEADERS, auth=FHIR_AUTH)
            
            if response.status_code != 200:
                return {"success": False, "status": response.status_code, "error": "Patient not found or error"}
            
            bundle = response.json()
            
            # Parse the bundle into structured data
            data = {
                "patient_id": patient_id,
                "success": True,
                "total_resources": bundle.get("total", len(bundle.get("entry", []))),
                "resources": {
                    "Patient": [],
                    "Condition": [],
                    "Observation": [],
                    "Procedure": [],
                    "Other": []
                },
                "summary": {
                    "diagnosis": None,
                    "tnm_clinical": None,
                    "tnm_pathological": None,
                    "biomarkers": {},
                    "treatments": [],
                    "metastases": [],
                    "progression": [],
                    "recurrence": None
                }
            }
            
            for entry in bundle.get("entry", []):
                resource = entry.get("resource", {})
                resource_type = resource.get("resourceType", "Other")
                
                # Categorize by resource type
                if resource_type in data["resources"]:
                    data["resources"][resource_type].append(resource)
                else:
                    data["resources"]["Other"].append(resource)
                
                # Parse into summary
                self._parse_to_summary(resource, data["summary"])
            
            return data
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_to_summary(self, resource: Dict, summary: Dict):
        """Parse a FHIR resource into the summary structure."""
        resource_type = resource.get("resourceType")
        
        # Get code info
        code_info = resource.get("code", {})
        coding = code_info.get("coding", [{}])[0]
        code = coding.get("code", "")
        code_text = code_info.get("text", "")
        
        if resource_type == "Condition":
            # Check if it's a metastasis
            if code.startswith("METASTASIS") or "metastáz" in code_text.lower():
                summary["metastases"].append({
                    "code": code,
                    "description": code_text,
                    "date": resource.get("onsetDateTime"),
                    "body_site": resource.get("bodySite", [{}])[0].get("text")
                })
            elif code == "RECURRENCE" or "recidiv" in code_text.lower():
                summary["recurrence"] = {
                    "description": code_text,
                    "date": resource.get("onsetDateTime")
                }
            else:
                # Primary diagnosis
                summary["diagnosis"] = {
                    "code": code,
                    "description": code_text,
                    "date": resource.get("onsetDateTime")
                }
        
        elif resource_type == "Observation":
            value = (resource.get("valueString") or 
                     resource.get("valueQuantity", {}).get("value") or
                     resource.get("valueCodeableConcept", {}).get("text"))
            date = resource.get("effectiveDateTime")
            
            if code == "TNM_CLINICAL":
                summary["tnm_clinical"] = {"value": value, "date": date}
            elif code == "TNM_PATHOLOGICAL":
                summary["tnm_pathological"] = {"value": value, "date": date}
            elif code in ("ER", "PR", "HER2", "KI67"):
                summary["biomarkers"][code] = {"value": value, "date": date}
            elif code == "PROGRESSION":
                summary["progression"].append({"description": value, "date": date})
        
        elif resource_type == "Procedure":
            summary["treatments"].append({
                "code": code,
                "description": code_text,
                "date": resource.get("performedDateTime")
            })


# ============ SAMPLE DATA BASED ON YOUR TABLE ============
SAMPLE_DATA = {
    # Datum diagnózy → Condition
    "diagnosis": {
        "field_name": "Datum diagnózy",
        "value": "Invazivní duktální karcinom pravého prsu",
        "date": "2022-10-05"
    },
    
    # Klinická TNM → Observation
    "clinical_tnm": {
        "field_name": "Klinická TNM",
        "value": "cT2N0M0",
        "date": "2022-10-05"
    },
    
    # Patologická TNM → Observation
    "pathological_tnm": {
        "field_name": "Patologická TNM",
        "value": "pT2N1M0",
        "date": "2022-12-02"
    },
    
    # ER → Observation (percentage)
    "er": {
        "field_name": "Estrogen receptor (ER)",
        "value": "95%",
        "date": "2022-10-05"
    },
    
    # PR → Observation (percentage)
    "pr": {
        "field_name": "Progesterone receptor (PR)",
        "value": "80%",
        "date": "2022-10-05"
    },
    
    # HER2 → Observation (positive/negative)
    "her2": {
        "field_name": "HER2 status",
        "value": "negativní",
        "date": "2022-10-05"
    },
    
    # Ki-67 → Observation (percentage)
    "ki67": {
        "field_name": "Ki-67 index",
        "value": "25%",
        "date": "2022-10-05"
    },
    
    # Léčba mimo MOÚ → Procedure
    "external_treatment": {
        "field_name": "Léčba mimo MOÚ",
        "value": "Chemoterapie v okresní nemocnici Brno-venkov",
        "date": "2022-11-15"
    },
    
    # Progrese → ClinicalImpression/Observation
    "progression": {
        "field_name": "Progrese onemocnění",
        "value": "Progrese v oblasti jater, nový ložiskový nález",
        "date": "2023-06-20"
    },
    
    # Recidiva → Condition
    "recurrence": {
        "field_name": "Recidiva",
        "value": "Lokální recidiva v oblasti jizvy po mastektomii",
        "date": "2024-01-10"
    },
    
    # Metastázy → Condition with body site
    "metastasis_liver": {
        "field_name": "Vzdálené metastázy - játra",
        "value": "Mnohočetné metastázy v játrech, největší 3.2cm",
        "date": "2023-08-15"
    },
    
    "metastasis_bone": {
        "field_name": "Vzdálené metastázy - kosti",
        "value": "Metastázy v bederní páteři L2-L4",
        "date": "2023-08-15"
    },
}


def run_all_samples(send_to_server: bool = False):
    """Run pipeline on all sample data."""
    pipeline = SimpleFHIRPipeline()
    patient_id = "HACK111"
    
    print("=" * 60)
    print(f"Running FHIR ingestion for patient: {patient_id}")
    print(f"Code system: {CODE_SYSTEM}")
    print("=" * 60)
    
    for key, sample in SAMPLE_DATA.items():
        print(f"\n--- {key.upper()} ---")
        
        result = pipeline.ingest(
            patient_id=patient_id,
            field_name=sample["field_name"],
            value=sample["value"],
            date=sample["date"],
            send_to_server=send_to_server
        )
        
        print(f"Field: {sample['field_name']}")
        print(f"Value: {sample['value']}")
        
        # Show code matching result
        if result.matched_code:
            print(f"→ Matched Code: {result.matched_code.code}")
            print(f"→ Confidence: {result.matched_code.confidence:.0%}")
        
        print(f"→ Resource: {result.resource_type}")
        print(f"→ Success: {'✅' if result.success else '❌'}")
        
        if result.error:
            print(f"→ Error: {result.error}")
        
        # Show server response details for failures
        if not result.success and result.server_response:
            print(f"→ HTTP Status: {result.server_response.get('status')}")
            error_response = result.server_response.get('response', {})
            
            # FHIR OperationOutcome contains 'issue' array with error details
            if 'issue' in error_response:
                for issue in error_response['issue']:
                    severity = issue.get('severity', 'error')
                    diagnostics = issue.get('diagnostics', '')
                    details = issue.get('details', {}).get('text', '')
                    print(f"   ⚠ [{severity}] {diagnostics or details or 'Unknown error'}")
            
            # Show the FHIR JSON that was sent (for debugging)
            if result.fhir_json:
                print(f"→ Sent JSON:\n{json.dumps(result.fhir_json, indent=2)}")
        
        elif result.fhir_json:
            # Show the standardized code in FHIR (success case)
            fhir = result.fhir_json
            if "code" in fhir:
                coding = fhir["code"].get("coding", [{}])[0]
                print(f"→ FHIR code: {coding.get('system', '')}|{coding.get('code', '')}")
    
    print("\n" + "=" * 60)
    print("Done! Set send_to_server=True to actually push to FHIR server.")
    print("=" * 60)


def show_available_codes():
    """Show all available standardized codes."""
    pipeline = SimpleFHIRPipeline()
    print("\n=== AVAILABLE CODES (from fhir_codes.csv) ===\n")
    for code in pipeline.list_codes():
        print(f"  {code['code']:20} → {code['description']} ({code['resource_type']})")


# ============ QUICK TEST ============
if __name__ == "__main__":
    # Show available codes
    # show_available_codes()
    
    # Run all samples (dry run by default)
    # run_all_samples(send_to_server=True)
    
    # ============ PATIENT MANAGEMENT EXAMPLES ============
    
    # Ensure patient exists (create if not)
    # pipeline = SimpleFHIRPipeline()
    # patient_result = pipeline.ensure_patient("HACK0111")
    # if patient_result.get("created"):
    #     print(f"✅ Created new patient: HACK0111")
    # elif patient_result.get("exists"):
    #     print(f"ℹ️ Patient already exists: HACK0111")
    # else:
    #     print(f"❌ Error: {patient_result.get('error')}")
    
    # Get all data for a patient
    pipeline = SimpleFHIRPipeline()
    patient_data = pipeline.get_patient_data("HACK01")
    if patient_data.get("success"):
        print(f"\n=== PATIENT DATA: HACK01 ===")
        print(f"Total resources: {patient_data['total_resources']}")
        print(f"\nResource counts:")
        for rtype, resources in patient_data['resources'].items():
            if resources:
                print(f"  {rtype}: {len(resources)}")
        print(f"\nSummary:")
        summary = patient_data['summary']
        if summary['diagnosis']:
            print(f"  Diagnosis: {summary['diagnosis']['description']} ({summary['diagnosis']['date']})")
        if summary['tnm_clinical']:
            print(f"  Clinical TNM: {summary['tnm_clinical']['value']}")
        if summary['tnm_pathological']:
            print(f"  Pathological TNM: {summary['tnm_pathological']['value']}")
        for marker, data in summary['biomarkers'].items():
            print(f"  {marker}: {data['value']}")
        for treatment in summary['treatments']:
            print(f"  Treatment: {treatment['description']} ({treatment['date']})")
        for meta in summary['metastases']:
            print(f"  Metastasis: {meta['description']} ({meta['date']})")
    else:
        print(f"❌ Error: {patient_data.get('error')}")
    
    # # Test single field with full JSON output:
    # pipeline = SimpleFHIRPipeline()
    # result = pipeline.ingest(
    #     patient_id="TEST001",
    #     field_name="HER2 receptor status",
    #     value="negative",
    #     date="2024-01-15",
    #     send_to_server=False
    # )
    # print(f"\nMatched: {result.matched_code}")
    # print(f"FHIR JSON:\n{json.dumps(result.fhir_json, indent=2)}")


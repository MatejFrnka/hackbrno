import pandas as pd
import typing


class LLMBackend:
    def process_patient(self, patient: pd.DataFrame):
        # TODO
        return {'diagnosis_date': [True, True, False], 'progression': [False, True, False]}

    def summarize_patient(self, patient: pd.DataFrame, processed_data) -> str:
        # TODO
        return 'Patient is ...'

    # Each patient is a tuple of the original data, processed data (from process_patient())
    # and patient summary (from summarize_patient())
    def summarize_batch(self, patients: typing.List[typing.Tuple[pd.DataFrame, typing.Any, str]]) -> str:
        # TODO
        return 'You have 10 patients ...'

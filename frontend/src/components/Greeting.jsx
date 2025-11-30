import { getGreetingKey } from '../utils/timeUtils';
import { useTranslation } from '../i18n/useTranslation';

const Greeting = () => {
    const { t } = useTranslation();

    return (
        <h1 className="text-6xl font-bold text-slate-900 tracking-tight mb-20 mt-10 text-center">
            {t(getGreetingKey())}
        </h1>
    );
};

export default Greeting;


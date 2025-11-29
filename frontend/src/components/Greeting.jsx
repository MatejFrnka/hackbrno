import { getGreeting } from '../utils/timeUtils';

const Greeting = () => {
    return (
        <h1 className="text-5xl font-semibold text-slate-900 tracking-tight mb-2">
            {getGreeting()}
        </h1>
    );
};

export default Greeting;


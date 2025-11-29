import { getGreeting } from '../utils/timeUtils';

const Greeting = () => {
    return (
        <h1 className="text-6xl font-bold text-slate-900 tracking-tight mb-20 mt-10 text-center">
            {getGreeting()}
        </h1>
    );
};

export default Greeting;


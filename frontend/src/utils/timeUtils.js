export const getGreetingKey = () => {
    const hour = new Date().getHours();

    if (hour >= 5 && hour < 12) {
        return 'greeting.morning';
    } else if (hour >= 12 && hour < 17) {
        return 'greeting.afternoon';
    } else if (hour >= 17 && hour < 22) {
        return 'greeting.evening';
    } else {
        return 'greeting.night';
    }
};


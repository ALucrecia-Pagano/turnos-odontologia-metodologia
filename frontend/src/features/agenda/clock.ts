export interface Clock {
  now(): Date;
}

export const systemClock: Clock = {
  now(): Date {
    return new Date();
  },
};

export function createFixedClock(instant: Date | string): Clock {
  const fixedTime = (typeof instant === "string" ? new Date(instant) : instant).getTime();
  return {
    now(): Date {
      return new Date(fixedTime);
    },
  };
}

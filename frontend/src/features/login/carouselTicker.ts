export type CarouselTicker = (callback: () => void) => () => void;

export function createIntervalTicker(intervalMs: number): CarouselTicker {
  return (callback) => {
    if (typeof window === "undefined") {
      return () => {};
    }
    const intervalId = window.setInterval(callback, intervalMs);
    return () => {
      window.clearInterval(intervalId);
    };
  };
}

import { setupAlarmListeners } from "./alarms";
import { setupMessageListeners } from "./messages";
import { observerEngine } from "./observer-engine";

export default defineBackground(() => {
  console.log("[Background Service Worker] Initialized.");

  // Initialize modular features
  setupAlarmListeners();
  setupMessageListeners();
  observerEngine();
});

// Servo repaints the whole page every frame an animation or a clip runs, which a handheld
// without a GPU draws on its CPU.
export const SPARE_FRAMES = navigator.userAgent.includes("Servo/");

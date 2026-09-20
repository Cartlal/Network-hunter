import type { Device } from "../types";

export function deviceName(device: Device): string {
  return device.custom_name || device.hostname || device.ip;
}

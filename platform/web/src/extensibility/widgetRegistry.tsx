import { type ComponentType } from "react";
import { ObjectContextWidget } from "./widgets/ObjectContextWidget";

const registry: Record<string, ComponentType<Record<string, string>>> = {
  "builtin.objectContext": ObjectContextWidget,
};

export function getWidgetComponent(widgetKey: string): ComponentType<Record<string, string>> | null {
  return registry[widgetKey] ?? null;
}

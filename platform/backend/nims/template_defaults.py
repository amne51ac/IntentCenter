"""Default object template definitions (builtin fields only; custom fields added via UI)."""

from __future__ import annotations

from typing import Any

# resourceType -> definition document
BASE_TEMPLATE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "Location": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "slug", "builtin": True, "label": "Slug", "type": "string", "required": True, "apiKey": "slug"},
            {
                "key": "locationTypeId",
                "builtin": True,
                "label": "Location type ID",
                "type": "uuid",
                "required": True,
                "apiKey": "locationTypeId",
            },
            {"key": "parentId", "builtin": True, "label": "Parent location ID", "type": "uuid", "apiKey": "parentId"},
            {"key": "description", "builtin": True, "label": "Description", "type": "textarea", "apiKey": "description"},
        ],
    },
    "Rack": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "locationId", "builtin": True, "label": "Location ID", "type": "uuid", "required": True, "apiKey": "locationId"},
            {"key": "uHeight", "builtin": True, "label": "U height", "type": "number", "apiKey": "uHeight"},
        ],
    },
    "Device": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "deviceTypeId", "builtin": True, "label": "Device type ID", "type": "uuid", "required": True, "apiKey": "deviceTypeId"},
            {"key": "deviceRoleId", "builtin": True, "label": "Device role ID", "type": "uuid", "required": True, "apiKey": "deviceRoleId"},
            {"key": "rackId", "builtin": True, "label": "Rack ID", "type": "uuid", "apiKey": "rackId"},
            {"key": "serialNumber", "builtin": True, "label": "Serial", "type": "string", "apiKey": "serialNumber"},
            {"key": "positionU", "builtin": True, "label": "Position (U)", "type": "number", "apiKey": "positionU"},
            {"key": "face", "builtin": True, "label": "Face", "type": "string", "apiKey": "face"},
            {
                "key": "status",
                "builtin": True,
                "label": "Status",
                "type": "select",
                "options": ["PLANNED", "STAGED", "ACTIVE", "DECOMMISSIONED"],
                "apiKey": "status",
            },
        ],
    },
    "Vrf": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "rd", "builtin": True, "label": "Route distinguisher", "type": "string", "apiKey": "rd"},
        ],
    },
    "Prefix": {
        "version": 1,
        "fields": [
            {"key": "vrfId", "builtin": True, "label": "VRF ID", "type": "uuid", "required": True, "apiKey": "vrfId"},
            {"key": "cidr", "builtin": True, "label": "CIDR", "type": "string", "required": True, "apiKey": "cidr"},
            {"key": "description", "builtin": True, "label": "Description", "type": "textarea", "apiKey": "description"},
            {"key": "parentId", "builtin": True, "label": "Parent prefix ID", "type": "uuid", "apiKey": "parentId"},
        ],
    },
    "IpAddress": {
        "version": 1,
        "fields": [
            {"key": "prefixId", "builtin": True, "label": "Prefix ID", "type": "uuid", "required": True, "apiKey": "prefixId"},
            {"key": "address", "builtin": True, "label": "Address", "type": "string", "required": True, "apiKey": "address"},
            {"key": "description", "builtin": True, "label": "Description", "type": "string", "apiKey": "description"},
            {"key": "interfaceId", "builtin": True, "label": "Interface ID", "type": "uuid", "apiKey": "interfaceId"},
        ],
    },
    "Vlan": {
        "version": 1,
        "fields": [
            {"key": "vid", "builtin": True, "label": "VID", "type": "number", "required": True, "apiKey": "vid"},
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "vlanGroupId", "builtin": True, "label": "VLAN group ID", "type": "uuid", "apiKey": "vlanGroupId"},
        ],
    },
    "Provider": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "asn", "builtin": True, "label": "ASN", "type": "number", "apiKey": "asn"},
        ],
    },
    "Circuit": {
        "version": 1,
        "fields": [
            {"key": "providerId", "builtin": True, "label": "Provider ID", "type": "uuid", "required": True, "apiKey": "providerId"},
            {"key": "cid", "builtin": True, "label": "Circuit ID", "type": "string", "required": True, "apiKey": "cid"},
            {"key": "bandwidthMbps", "builtin": True, "label": "Bandwidth (Mbps)", "type": "number", "apiKey": "bandwidthMbps"},
            {
                "key": "status",
                "builtin": True,
                "label": "Status",
                "type": "select",
                "options": ["PLANNED", "ACTIVE", "DECOMMISSIONED"],
                "apiKey": "status",
            },
            {"key": "aSideNotes", "builtin": True, "label": "A-side notes", "type": "textarea", "apiKey": "aSideNotes"},
            {"key": "zSideNotes", "builtin": True, "label": "Z-side notes", "type": "textarea", "apiKey": "zSideNotes"},
            {
                "key": "circuitDiversityGroupId",
                "builtin": True,
                "label": "Circuit diversity group ID",
                "type": "uuid",
                "apiKey": "circuitDiversityGroupId",
            },
        ],
    },
    "CircuitDiversityGroup": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "slug", "builtin": True, "label": "Slug", "type": "string", "required": True, "apiKey": "slug"},
            {"key": "description", "builtin": True, "label": "Description", "type": "textarea", "apiKey": "description"},
        ],
    },
    "ServiceInstance": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "serviceType", "builtin": True, "label": "Service type", "type": "string", "required": True, "apiKey": "serviceType"},
            {"key": "customerRef", "builtin": True, "label": "Customer ref", "type": "string", "apiKey": "customerRef"},
        ],
    },
    "JobDefinition": {
        "version": 1,
        "fields": [
            {"key": "key", "builtin": True, "label": "Key", "type": "string", "required": True, "apiKey": "key"},
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "description", "builtin": True, "label": "Description", "type": "textarea", "apiKey": "description"},
            {"key": "requiresApproval", "builtin": True, "label": "Requires approval", "type": "boolean", "apiKey": "requiresApproval"},
        ],
    },
    # Extended catalog (schema Phase 2); tenant boundary remains Organization.
    "DynamicGroup": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "slug", "builtin": True, "label": "Slug", "type": "string", "required": True, "apiKey": "slug"},
            {"key": "description", "builtin": True, "label": "Description", "type": "textarea", "apiKey": "description"},
        ],
    },
    "VirtualChassis": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "domainId", "builtin": True, "label": "Domain ID", "type": "string", "apiKey": "domainId"},
        ],
    },
    "Controller": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "deviceId", "builtin": True, "label": "Device ID", "type": "uuid", "apiKey": "deviceId"},
            {"key": "role", "builtin": True, "label": "Role", "type": "string", "apiKey": "role"},
        ],
    },
    "DeviceRedundancyGroup": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "protocol", "builtin": True, "label": "Protocol", "type": "string", "apiKey": "protocol"},
        ],
    },
    "InterfaceRedundancyGroup": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "protocol", "builtin": True, "label": "Protocol", "type": "string", "apiKey": "protocol"},
        ],
    },
    "PowerPanel": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "locationId", "builtin": True, "label": "Location ID", "type": "uuid", "required": True, "apiKey": "locationId"},
        ],
    },
    "PowerFeed": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "powerPanelId", "builtin": True, "label": "Power panel ID", "type": "uuid", "apiKey": "powerPanelId"},
            {"key": "voltage", "builtin": True, "label": "Voltage", "type": "number", "apiKey": "voltage"},
            {"key": "amperage", "builtin": True, "label": "Amperage", "type": "number", "apiKey": "amperage"},
        ],
    },
    "CloudNetwork": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "cloudProvider", "builtin": True, "label": "Cloud provider", "type": "string", "apiKey": "cloudProvider"},
        ],
    },
    "CloudService": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "cloudNetworkId", "builtin": True, "label": "Cloud network ID", "type": "uuid", "apiKey": "cloudNetworkId"},
            {"key": "serviceType", "builtin": True, "label": "Service type", "type": "string", "apiKey": "serviceType"},
        ],
    },
    "WirelessNetwork": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "ssid", "builtin": True, "label": "SSID", "type": "string", "apiKey": "ssid"},
        ],
    },
    "Vpn": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "vpnType", "builtin": True, "label": "VPN type", "type": "string", "required": True, "apiKey": "vpnType"},
        ],
    },
    "Cluster": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "clusterType", "builtin": True, "label": "Cluster type", "type": "string", "apiKey": "clusterType"},
        ],
    },
    "VirtualMachine": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "clusterId", "builtin": True, "label": "Cluster ID", "type": "uuid", "apiKey": "clusterId"},
        ],
    },
    "MplsDomain": {
        "version": 1,
        "fields": [
            {"key": "name", "builtin": True, "label": "Name", "type": "string", "required": True, "apiKey": "name"},
            {"key": "rd", "builtin": True, "label": "Route distinguisher", "type": "string", "apiKey": "rd"},
        ],
    },
}

SUPPORTED_RESOURCE_TYPES = tuple(sorted(BASE_TEMPLATE_DEFINITIONS.keys()))

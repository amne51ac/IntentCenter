import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { apiJson } from "./api/client";
import { AppShell } from "./layout/AppShell";
import { CircuitFormPage } from "./pages/circuits/CircuitFormPage";
import { CircuitsPage } from "./pages/circuits/Circuits";
import { ProviderFormPage } from "./pages/circuits/ProviderFormPage";
import { ProvidersPage } from "./pages/circuits/Providers";
import { Dashboard } from "./pages/Dashboard";
import { DeviceFormPage } from "./pages/dcim/DeviceFormPage";
import { DevicesPage } from "./pages/dcim/Devices";
import { LocationFormPage } from "./pages/dcim/LocationFormPage";
import { LocationsPage } from "./pages/dcim/Locations";
import { RackFormPage } from "./pages/dcim/RackFormPage";
import { RacksPage } from "./pages/dcim/Racks";
import { IpAddressFormPage } from "./pages/ipam/IpAddressFormPage";
import { IpAddressesPage } from "./pages/ipam/IpAddresses";
import { PrefixFormPage } from "./pages/ipam/PrefixFormPage";
import { PrefixesPage } from "./pages/ipam/Prefixes";
import { VlanFormPage } from "./pages/ipam/VlanFormPage";
import { VlansPage } from "./pages/ipam/Vlans";
import { VrfsPage } from "./pages/ipam/Vrfs";
import { LoginPage } from "./pages/Login";
import { AuditPage } from "./pages/platform/Audit";
import { ObjectTemplatesPage } from "./pages/platform/ObjectTemplates";
import { JobFormPage } from "./pages/platform/JobFormPage";
import { JobRunFormPage } from "./pages/platform/JobRunFormPage";
import { JobRunsPage } from "./pages/platform/JobRuns";
import { JobsPage } from "./pages/platform/Jobs";
import { ServiceFormPage } from "./pages/platform/ServiceFormPage";
import { ServicesPage } from "./pages/platform/Services";
import { ObjectViewPage } from "./pages/inventory/ObjectViewPage";
import { CatalogListPage } from "./pages/inventory/CatalogListPage";
import { CatalogItemCreatePage } from "./pages/inventory/CatalogItemCreatePage";
import { CatalogItemEditPage } from "./pages/inventory/CatalogItemEditPage";
import { ObjectTemplateEditPage } from "./pages/platform/ObjectTemplateEditPage";
import { VrfFormPage } from "./pages/ipam/VrfFormPage";
import { ComingSoonPage } from "./pages/ComingSoonPage";
import { BlockLoader } from "./components/Loader";

function RequireAuth({ children }: { children: ReactNode }) {
  const session = useQuery({
    queryKey: ["me"],
    queryFn: () => apiJson<unknown>("/v1/me"),
    retry: false,
  });

  if (session.isLoading) {
    return (
      <div className="main">
        <BlockLoader label="Loading session…" />
      </div>
    );
  }

  if (session.isError) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="dcim/locations/new" element={<LocationFormPage />} />
        <Route path="dcim/locations/:locationId/edit" element={<LocationFormPage />} />
        <Route path="dcim/locations" element={<LocationsPage />} />
        <Route path="dcim/racks/new" element={<RackFormPage />} />
        <Route path="dcim/racks/:rackId/edit" element={<RackFormPage />} />
        <Route path="dcim/racks" element={<RacksPage />} />
        <Route path="dcim/devices/new" element={<DeviceFormPage />} />
        <Route path="dcim/devices/:deviceId/edit" element={<DeviceFormPage />} />
        <Route path="dcim/devices" element={<DevicesPage />} />
        <Route path="ipam/vrfs/new" element={<VrfFormPage />} />
        <Route path="ipam/vrfs/:vrfId/edit" element={<VrfFormPage />} />
        <Route path="ipam/vrfs" element={<VrfsPage />} />
        <Route path="ipam/prefixes/new" element={<PrefixFormPage />} />
        <Route path="ipam/prefixes/:prefixId/edit" element={<PrefixFormPage />} />
        <Route path="ipam/prefixes" element={<PrefixesPage />} />
        <Route path="ipam/ip-addresses/new" element={<IpAddressFormPage />} />
        <Route path="ipam/ip-addresses/:ipAddressId/edit" element={<IpAddressFormPage />} />
        <Route path="ipam/ip-addresses" element={<IpAddressesPage />} />
        <Route path="ipam/vlans/new" element={<VlanFormPage />} />
        <Route path="ipam/vlans/:vlanId/edit" element={<VlanFormPage />} />
        <Route path="ipam/vlans" element={<VlansPage />} />
        <Route path="circuits/providers/new" element={<ProviderFormPage />} />
        <Route path="circuits/providers/:providerId/edit" element={<ProviderFormPage />} />
        <Route path="circuits/providers" element={<ProvidersPage />} />
        <Route path="circuits/circuits/new" element={<CircuitFormPage />} />
        <Route path="circuits/circuits/:circuitId/edit" element={<CircuitFormPage />} />
        <Route path="circuits/circuits" element={<CircuitsPage />} />
        <Route path="platform/jobs/new" element={<JobFormPage />} />
        <Route path="platform/jobs/:jobId/edit" element={<JobFormPage />} />
        <Route path="platform/jobs" element={<JobsPage />} />
        <Route path="platform/job-runs/new" element={<JobRunFormPage />} />
        <Route path="platform/job-runs" element={<JobRunsPage />} />
        <Route path="platform/services/new" element={<ServiceFormPage />} />
        <Route path="platform/services/:serviceId/edit" element={<ServiceFormPage />} />
        <Route path="platform/services" element={<ServicesPage />} />
        <Route path="platform/audit" element={<AuditPage />} />
        <Route path="platform/object-templates/:templateId/edit" element={<ObjectTemplateEditPage />} />
        <Route path="platform/object-templates" element={<ObjectTemplatesPage />} />
        <Route path="inventory/:catalogSlug/new" element={<CatalogItemCreatePage />} />
        <Route path="inventory/:catalogSlug/:itemId/edit" element={<CatalogItemEditPage />} />
        <Route path="inventory/:catalogSlug" element={<CatalogListPage />} />
        <Route path="coming-soon/:slug" element={<ComingSoonPage />} />
        <Route path="o/:resourceType/:resourceId" element={<ObjectViewPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

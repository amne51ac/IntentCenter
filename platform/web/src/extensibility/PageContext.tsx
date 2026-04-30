import { createContext, useContext, type ReactNode } from "react";

export type PageContextValue = {
  pageId: string;
  page: {
    pageId: string;
    params: Record<string, string | undefined>;
    resourceType?: string;
    resourceId?: string;
  };
  resource: Record<string, unknown> | null;
  user: { id: string; role: string } | null;
  organization: { id: string; name: string; slug: string } | null;
};

const PageContext = createContext<PageContextValue | null>(null);

export function PageContextProvider({
  value,
  children,
}: {
  value: PageContextValue;
  children: ReactNode;
}) {
  return <PageContext.Provider value={value}>{children}</PageContext.Provider>;
}

export function usePageContext(): PageContextValue {
  const c = useContext(PageContext);
  if (!c) {
    throw new Error("usePageContext must be used under PageContextProvider");
  }
  return c;
}

export function useOptionalPageContext(): PageContextValue | null {
  return useContext(PageContext);
}

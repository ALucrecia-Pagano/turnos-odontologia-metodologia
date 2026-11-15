export type CatalogSectionKey = "profesionales" | "sillones" | "prestaciones";

export interface CatalogColumn<T> {
  readonly header: string;
  readonly render: (item: T) => string | number | null | undefined;
}

export interface CatalogFieldConfig {
  readonly name: string;
  readonly label: string;
  readonly type: "text" | "number";
  readonly required?: boolean;
  readonly maxLength?: number;
  readonly placeholder?: string;
}

export interface CatalogConfig<T extends { id: string; active: boolean }> {
  readonly key: CatalogSectionKey;
  readonly label: string;
  readonly entityNameSingular: string;
  readonly gender: "m" | "f";
  readonly apiPath: string;
  readonly columns: readonly CatalogColumn<T>[];
  readonly fields: readonly CatalogFieldConfig[];
  readonly toPayload: (formData: Record<string, string>) => Record<string, unknown>;
  readonly toFormData: (item: T) => Record<string, string>;
}

export interface ProfessionalItem {
  readonly id: string;
  readonly fullName: string;
  readonly active: boolean;
  readonly licenseNumber: string | null;
}

export interface ChairItem {
  readonly id: string;
  readonly name: string;
  readonly active: boolean;
}

export interface ServiceItem {
  readonly id: string;
  readonly name: string;
  readonly defaultDurationMin: number;
  readonly active: boolean;
}

export type AnyCatalogItem = ProfessionalItem | ChairItem | ServiceItem;

export const PROFESSIONAL_CONFIG: CatalogConfig<ProfessionalItem> = {
  key: "profesionales",
  label: "Profesionales",
  entityNameSingular: "profesional",
  gender: "m",
  apiPath: "/professionals",
  columns: [
    { header: "Nombre", render: (item) => item.fullName },
    { header: "Matrícula", render: (item) => item.licenseNumber ?? "Sin dato" },
  ],
  fields: [
    {
      name: "fullName",
      label: "Nombre",
      type: "text",
      required: true,
      maxLength: 255,
      placeholder: "Ej: Dra. María González",
    },
    {
      name: "licenseNumber",
      label: "Matrícula",
      type: "text",
      required: false,
      maxLength: 50,
      placeholder: "Ej: MN 12345 (opcional)",
    },
  ],
  toPayload: (formData) => ({
    fullName: formData["fullName"] ?? "",
    licenseNumber: formData["licenseNumber"]?.trim() ? formData["licenseNumber"].trim() : null,
  }),
  toFormData: (item) => ({
    fullName: item.fullName,
    licenseNumber: item.licenseNumber ?? "",
  }),
};

export const CHAIR_CONFIG: CatalogConfig<ChairItem> = {
  key: "sillones",
  label: "Sillones",
  entityNameSingular: "sillón",
  gender: "m",
  apiPath: "/chairs",
  columns: [{ header: "Nombre", render: (item) => item.name }],
  fields: [
    {
      name: "name",
      label: "Nombre",
      type: "text",
      required: true,
      maxLength: 255,
      placeholder: "Ej: Sillón 1",
    },
  ],
  toPayload: (formData) => ({
    name: formData["name"] ?? "",
  }),
  toFormData: (item) => ({
    name: item.name,
  }),
};

export const SERVICE_CONFIG: CatalogConfig<ServiceItem> = {
  key: "prestaciones",
  label: "Prestaciones",
  entityNameSingular: "prestación",
  gender: "f",
  apiPath: "/services",
  columns: [
    { header: "Nombre", render: (item) => item.name },
    { header: "Duración (min)", render: (item) => item.defaultDurationMin },
  ],
  fields: [
    {
      name: "name",
      label: "Nombre",
      type: "text",
      required: true,
      maxLength: 255,
      placeholder: "Ej: Limpieza dental",
    },
    {
      name: "defaultDurationMin",
      label: "Duración (min)",
      type: "number",
      required: true,
      placeholder: "Ej: 30",
    },
  ],
  toPayload: (formData) => ({
    name: formData["name"] ?? "",
    defaultDurationMin: Number(formData["defaultDurationMin"]),
  }),
  toFormData: (item) => ({
    name: item.name,
    defaultDurationMin: String(item.defaultDurationMin),
  }),
};

export const CATALOG_CONFIGS: Record<CatalogSectionKey, CatalogConfig<AnyCatalogItem>> = {
  profesionales: PROFESSIONAL_CONFIG as unknown as CatalogConfig<AnyCatalogItem>,
  sillones: CHAIR_CONFIG as unknown as CatalogConfig<AnyCatalogItem>,
  prestaciones: SERVICE_CONFIG as unknown as CatalogConfig<AnyCatalogItem>,
};

export const CATALOG_SECTIONS: readonly { readonly key: CatalogSectionKey; readonly label: string }[] = [
  { key: "profesionales", label: "Profesionales" },
  { key: "sillones", label: "Sillones" },
  { key: "prestaciones", label: "Prestaciones" },
];

export function resolveCatalogConfig(key: string | null): CatalogConfig<AnyCatalogItem> {
  if (key === "sillones" || key === "prestaciones") {
    return CATALOG_CONFIGS[key];
  }
  return CATALOG_CONFIGS.profesionales;
}

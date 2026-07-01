export type PolicyDocumentOption = {
  document_id: number;
  policy_name: string;
  policy_category: string;
  responsible_department: string | null;
  latest_version_id: number | null;
  latest_version_label: string | null;
};

export type PolicyDocumentOptionList = {
  items: PolicyDocumentOption[];
};

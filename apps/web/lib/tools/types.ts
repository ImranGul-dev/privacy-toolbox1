export type ToolKind = 'image' | 'pdf' | 'office' | 'media' | 'archive' | 'verify' | 'ai';
export type ToolAction = 'scan' | 'clean' | 'verify';

export type ToolInfo = {
  slug: string;
  apiToolId: string;
  title: string;
  shortTitle: string;
  endpoint: string;
  defaultAction: ToolAction;
  scanAction: ToolAction;
  cleanAction?: ToolAction;
  supportsClean: boolean;
  kind: ToolKind;
  desc: string;
  formats: string;
  acceptedFileTypes: string[];
  badge?: string;
  action?: string;
  faq: { q: string; a: string }[];
};

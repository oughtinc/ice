export type TextParam = {
  kind: "TextParam";
  name: string;
  value: string | null;
  label: string;
  default_value: string | null;
};

export type IntParam = {
  kind: "IntParam";
  name: string;
  value: int | null;
  label: string;
  default_value: nt | null;
};

export type IdParam = {
  kind: "IdParam";
  name: string;
  value: string | null;
  label: string;
  default_value: string | null;
};

export type ActionParam = TextParam | IntParam | IdParam;

export type Action = {
  kind: string;
  params: ActionParam[];
  label: string;
};

export type RowId = string;
export type CardId = string;
export type PathId = string;

export interface Row {
  id: RowId;
  kind: string;
  // content varies by row export type
}

export interface TextRow extends Row {
  kind: "Text";
  text: string;
}

export interface PaperRow extends Row {
  kind: "Paper";
  title: string | null;
  authors: string[];
  year: number | null;
  citations: number | null;
  raw_data: Record<string, unknown>;
}

export type Card = {
  id: CardId;
  rows: Row[];
  nextId: CardId | null;
  prevId: CardId | null;
};

export type View = {
  selected_row_ids: Record<RowId, boolean>;
  focused_row_index: number | null;
};

export type Path = {
  id: PathId;
  label: string;
  head_card_id: CardId;
  view: View;
};

export type HydratedPath = {
  id: PathId;
  label: string;
  head_card: Card;
  view: View;
};

export type Frontier = {
  paths: Record<PathId, HydratedPath>;
  focus_path_id: PathId;
};

// Same as Frontier, but used to signpost places where we might not
// return a full replacement, i.e. paths will only include paths that
// are being modified.
export type PartialFrontier = Frontier;

export type Workspace = {
  cards: Record<CardId, Card>;
  paths: Record<PathId, Path>;
  focus_path_id: PathId;
  available_actions: Action[];
};

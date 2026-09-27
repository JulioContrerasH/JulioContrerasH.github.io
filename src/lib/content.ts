import { parse } from 'yaml';
import profileRaw from '../../data/profile.yaml?raw';
import publicationsRaw from '../../data/publications.yaml?raw';
import talksRaw from '../../data/talks.yaml?raw';
import uiRaw from '../../data/ui.yaml?raw';

export type Lang = 'es' | 'en';

export interface Affiliation {
  id: string;
  org: string;
  dept?: string | null;
  role?: string | null;
  dates?: string | null;
  source?: string;
}

export interface Education {
  degree: string;
  degree_en?: string | null;
  org: string;
  dates?: string | null;
  details?: string | null;
  details_en?: string | null;
  source?: string;
}

export interface Experience {
  org: string;
  role: string;
  role_en?: string | null;
  dates?: string | null;
  details?: string | null;
  details_en?: string | null;
  source?: string;
}

export interface SkillGroup {
  family: string;
  items: string[];
}

export interface LanguageSkill {
  name: string;
  level: string;
}

export interface Certificate {
  name: string;
  year: number;
  url?: string | null;
}

export interface Profile {
  name: string;
  display_name: string;
  photo: string;
  email: string;
  location: { current: string; current_en?: string; origin: string; origin_en?: string };
  audience: string[];
  goal: string;
  site: { domain: string; languages: string[] };
  bio: { es: string; en: string; status?: string; tone?: string };
  affiliations: Affiliation[];
  education: Education[];
  experience: Experience[];
  skills: SkillGroup[];
  languages: LanguageSkill[];
  certificates: Certificate[];
  interests: { es: string[]; en: string[] };
  links: Record<string, string | null>;
}

export interface Project {
  id: string;
  order: number;
  title: string;
  title_en?: string | null;
  year: string | number | null;
  type: 'ground' | 'orbit';
  chapter: 'peru' | 'valencia' | 'ahora';
  chain_stage: string;
  include: boolean;
  section?: 'research' | 'software' | 'applied';
  role: string | null;
  role_en?: string | null;
  one_liner: string;
  one_liner_en?: string | null;
  coords: { lon: number; lat: number } | null;
  location: string | null;
  location_en?: string | null;
  image?: string | null;
  footprint?: [number, number, number, number] | null;
  global?: boolean;
  links: Record<string, string>;
  status: string;
}

export interface Publication {
  id: string;
  title: string;
  year: number;
  venue: string;
  doi: string | null;
  url: string | null;
  role: string | null;
  type: string;
}

export interface Talk {
  id: string;
  title: string | null;
  event: string;
  place: string | null;
  date: string;
  kind: string | null;
  role: string | null;
  links: Record<string, string>;
  source: string;
}

export interface UiStrings {
  site: { title: string; description: string };
  nav: Record<string, string>;
  hero: Record<string, string>;
  labels: Record<string, unknown>;
  sections: Record<string, string>;
  chapters: Record<'peru' | 'valencia' | 'ahora', { title: string; text: string }>;
}

// Los proyectos se mantienen como Markdown estilo Hugo: un .md por proyecto en
// src/content/projects/, con el frontmatter (datos) y el cuerpo libre debajo.
const projectSources = import.meta.glob('../content/projects/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

function parseFrontmatter(raw: string): Record<string, unknown> {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  return match ? (parse(match[1]) as Record<string, unknown>) : {};
}

const projectsAll = Object.values(projectSources).map(
  (raw) => parseFrontmatter(raw) as unknown as Project
);

export const profile: Profile = parse(profileRaw);
export const ui = parse(uiRaw) as Record<Lang, UiStrings>;
export function projectYear(project: Project): number {
  const years = String(project.year ?? '').match(/\d{4}/g);
  return years ? Number(years[years.length - 1]) : 0;
}

export const projects = projectsAll
  .filter((p) => p.include)
  .sort((a, b) => projectYear(b) - projectYear(a) || a.order - b.order);
export const research = projects.filter((p) => !p.section || p.section === 'research');
export const software = projects.filter((p) => p.section === 'software');
export const applied = projects.filter((p) => p.section === 'applied');
export const publications: Publication[] = (parse(publicationsRaw) as Publication[]).sort(
  (a, b) => b.year - a.year
);
export const talks: Talk[] = (parse(talksRaw) as Talk[]).sort((a, b) =>
  a.date < b.date ? 1 : -1
);

export const groundProjects = projects.filter((p) => p.type === 'ground' && p.coords);
export const orbitProjects = projects.filter((p) => p.type === 'orbit');

export function t(lang: Lang): UiStrings {
  return ui[lang];
}

export function linkLabel(lang: Lang, key: string): string {
  const labels = ui[lang].labels as Record<string, string>;
  return labels[key] ?? key.charAt(0).toUpperCase() + key.slice(1);
}

export function chapterProjects(chapter: Project['chapter']): Project[] {
  return projects.filter((p) => p.chapter === chapter);
}

export function localizedField(
  lang: Lang,
  item: Record<string, unknown>,
  field: string
): string {
  if (lang === 'en') {
    const en = item[`${field}_en`];
    if (typeof en === 'string' && en.length > 0) return en;
  }
  const value = item[field];
  return typeof value === 'string' ? value : '';
}

export function otherLang(lang: Lang): Lang {
  return lang === 'es' ? 'en' : 'es';
}

export function switchLangPath(lang: Lang, path: string): string {
  if (lang === 'en') {
    return path === '/' ? '/es/' : `/es${path}`;
  }
  return path.replace(/^\/es/, '') || '/';
}

export function localizedPath(lang: Lang, path: string): string {
  const clean = path.replace(/^\/|\/$/g, '');
  const prefix = lang === 'es' ? '/es' : '';
  return clean ? `${prefix}/${clean}/` : `${prefix}/`;
}

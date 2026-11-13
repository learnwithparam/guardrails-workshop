// Every page a learner can open. The audit visits each one at 1280 px and at 375 px wide.
export type Route = { name: string; path: string };

export const routes: Route[] = [{ name: "desk page", path: "/" }];

// Button verbs this course uses beyond the shared list, in lower case.
export const extraButtonVerbs: string[] = ["run"];

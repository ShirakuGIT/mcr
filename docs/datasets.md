# Object Dataset Notes

These are the most relevant external sources for replacing the current primitive proxies with household, grocery, kitchen, and clutter objects that fit the existing scenes.

## Recommended First Choices
1. YCB Object and Model Set
Why it fits: standardized household and manipulation objects, strong robotics adoption, textured meshes, and object categories that map well to cans, bottles, boxes, and tableware.
Link: https://registry.opendata.aws/ycb-benchmarks/

2. Google Scanned Objects
Why it fits: large collection of real consumer products and household items with meshes that are useful for cluttered tabletop scenes.
Link: https://app.gazebosim.org/OpenRobotics/fuel/collections/Google%20Scanned%20Objects

3. HOPE dataset in BOP
Why it fits: household object pose estimation benchmark assets, useful if you want a smaller curated set of realistic kitchen and pantry items.
Link: https://bop.felk.cvut.cz/datasets/

## Useful Secondary Sources
1. HouseCat6D
Why it fits: category-level household objects in realistic scenes. Better for finding category coverage and grasp/task inspiration than immediate drop-in simulation meshes.
Publication page: https://cris.fau.de/publications/330649139/

2. SG-Bot dataset
Why it fits: tabletop rearrangement scenes built from scanned household meshes, useful as a reference for scene composition and clutter layouts.
Link: https://sites.google.com/view/sg-bot/dataset

## Integration Guidance
1. Start with YCB for canonical benchmark objects in the kitchen and clutter scenes.
2. Use Google Scanned Objects when you want more visually specific grocery packaging.
3. Keep imported meshes in a dataset-specific subtree such as `assets/meshes/datasets/ycb/` or `assets/meshes/datasets/gso/`.
4. Store object placement and semantics in scene YAML rather than dedicated Python files.
5. Preserve the current primitive versions as fast-loading fallback scenes for planner debugging.

## Repo Wiring
1. Put raw downloads under `assets/datasets/`.
2. Create or update reusable presets in `configs/objects/`.
3. Point scenes at those presets with `object_libraries` plus `preset` fields.
4. Use `tabletop_kitchen_grocery_dataset_staging` as the first replacement target because it already mixes presets with a stand-in scanned asset slot.
5. `tabletop_kitchen_google_scanned_objects` now demonstrates three real imported Google scanned kitchen objects wired through reusable presets.
6. `tabletop_pantry_google_scanned_objects` now demonstrates real imported cereal, gum-bottle, and canned-drink package meshes.

## Version-Control Policy
1. Keep normalized, scene-ready assets only when they are actually referenced by presets or scenes.
2. Do not commit raw archives or temporary extraction directories; `.gitignore` is set up for ad-hoc pulls and local staging.
3. When you keep imported assets in-repo, add or update a `SOURCES.md` file beside that asset family.
4. Update this document when you add a new dataset source or a new normalization workflow.

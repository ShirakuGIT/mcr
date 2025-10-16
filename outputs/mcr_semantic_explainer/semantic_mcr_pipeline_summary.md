# Semantic MCR Run

- Standard path: start -> fragile_route_1 -> fragile_route_2 -> goal
- Standard subset: {fragile_vase,knife_block}
- Standard collision count: 2
- Standard semantic weight: 17.0
- Semantic path: start -> soft_route_1 -> soft_route_2 -> soft_route_3 -> goal
- Semantic subset: {cardboard_box,dish_towel,sponge}
- Semantic collision count: 3
- Semantic semantic weight: 3.0

Interpretation:
- Standard MCR prefers fewer collisions even if they are semantically severe.
- Semantic MCR prefers more benign collisions if their total consequence is lower.
- With history-dependent collision sets, one subset per vertex is not generally sufficient.
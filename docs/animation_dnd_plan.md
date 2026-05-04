# Modern Animations & Drag-and-Drop Implementation Plan

## Overview
This document outlines the multi-phase plan to introduce modern animations and drag-and-drop interactions to the DnD Westmarches Hub application using native web capabilities and Svelte 5 runes for state management.

## System Architecture & Class Design

### Drag-and-Drop System (`DragDropManager`)
We will use the HTML5 Drag and Drop API integrated with a central, abstractable state manager built on Svelte 5 `$state` runes.

```typescript
// Proposed concept for DragDropManager
export class DragDropManager<T> {
  // State
  public isDragging = $state(false);
  public currentPayload = $state<T | null>(null);

  // Handlers for draggable items
  public handleDragStart(event: DragEvent, payload: T) {
    this.isDragging = true;
    this.currentPayload = payload;
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'copyMove';
      event.dataTransfer.setData('application/json', JSON.stringify(payload));
    }
  }

  public handleDragEnd() {
    this.isDragging = false;
    this.currentPayload = null;
  }

  // Utilities for drop zones
  public isDroppable(event: DragEvent) {
    return event.dataTransfer?.types.includes('application/json');
  }
}
```

### Animation Components
Instead of heavy third-party libraries, we will use native CSS Transitions and 3D Transforms, wrapped in reusable Svelte components.

**`RewardCard.svelte`**:
- Encapsulates a 3D flip effect.
- Manages local state `isRevealed`.
- When clicked, toggles `isRevealed` applying a 180-degree `rotateY` transform.
- Renders `hint` on the front face, and `item/gold/xp` on the back face.

## Implementation Phases

### Phase 1: Foundation (Backend & State Models) [Current MVP]
1. **Database Update**: Add `is_hidden` (boolean) and `hint` (string) to `MissionReward` models.
2. **Core Abstractions**: Implement `DragDropManager` and reusable animation components (`RewardCard`).
3. **UI Integration**:
   - Apply `RewardCard` to the Mission Board.
   - Refactor Sessions Board to support dragging mission cards onto session slots to propose content.

### Phase 2: Enhanced Feedback (Future)
- Add spring animations for drag snap-back using `svelte/motion`.
- Implement visual drop zone indicators (highlighting valid slots when dragging begins).

### Phase 3: Broad Rollout (Future)
- Apply Drag-and-Drop to inventory management (equipping items).
- Apply Flip Cards to other hidden mechanics (e.g., Faction reputation reveals or unexplored map hexes).

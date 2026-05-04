export class DragDropManager<T> {
    isDragging = $state(false);
    currentPayload = $state<T | null>(null);

    handleDragStart(event: DragEvent, payload: T) {
        this.isDragging = true;
        this.currentPayload = payload;

        if (event.dataTransfer) {
            event.dataTransfer.effectAllowed = 'copyMove';
            event.dataTransfer.setData('application/json', JSON.stringify(payload));
        }
    }

    handleDragEnd() {
        this.isDragging = false;
        this.currentPayload = null;
    }

    isDroppable(event: DragEvent) {
        return event.dataTransfer?.types.includes('application/json');
    }

    getPayload(event: DragEvent): T | null {
        try {
            const data = event.dataTransfer?.getData('application/json');
            return data ? JSON.parse(data) : null;
        } catch {
            return null;
        }
    }
}

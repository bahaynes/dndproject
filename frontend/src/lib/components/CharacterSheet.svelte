<script lang="ts">
    import { auth, type Character, type User, login } from '$lib/auth';
    import { onMount } from 'svelte';
    import { get } from 'svelte/store';

    let character: Character | null = null;
    let isEditing = false;
    let editableName = '';
    let editableDescription = '';
    let error: string | null = null;
    let success: string | null = null;

    auth.subscribe(value => {
        if (value.user && value.user.character) {
            character = value.user.character;
            if (character) {
                editableName = character.name;
                editableDescription = character.description || '';
            }
        }
    });

    function toggleEditMode() {
        isEditing = !isEditing;
        // Reset any pending changes when exiting edit mode
        if (!isEditing && character) {
            editableName = character.name;
            editableDescription = character.description || '';
        }
        error = null;
        success = null;
    }

    async function handleSave() {
        if (!character) return;
        error = null;
        success = null;

        const authState = get(auth);
        if (!authState.token) {
            error = "Not authenticated.";
            return;
        }

        const response = await fetch(`http://localhost:8000/api/characters/${character.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authState.token}`
            },
            body: JSON.stringify({
                name: editableName,
                description: editableDescription
            })
        });

        if (response.ok) {
            const updatedCharacter = await response.json();
            // Update the character in the global user state
            const currentUser = get(auth).user;
            if (currentUser) {
                const updatedUser: User = { ...currentUser, character: updatedCharacter };
                login(updatedUser, authState.token);
            }
            success = "Character updated successfully!";
            isEditing = false;
        } else {
            const errorData = await response.json();
            error = errorData.detail || "Failed to update character.";
        }
    }

    async function handleImageUpload(event: Event) {
        const input = event.target as HTMLInputElement;
        if (!input.files || input.files.length === 0 || !character) {
            return;
        }
        const file = input.files[0];
        const formData = new FormData();
        formData.append('file', file);

        const authState = get(auth);
        if (!authState.token) {
            error = "Not authenticated.";
            return;
        }

        const response = await fetch(`http://localhost:8000/api/characters/${character.id}/image`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authState.token}`
            },
            body: formData
        });

        if (response.ok) {
            const updatedCharacter = await response.json();
            const currentUser = get(auth).user;
            if (currentUser) {
                const updatedUser: User = { ...currentUser, character: updatedCharacter };
                login(updatedUser, authState.token);
            }
            success = "Image updated successfully!";
        } else {
            error = "Failed to upload image.";
        }
    }

</script>

{#if character}
    <div class="bg-white shadow-md rounded-lg p-6 relative">
        <!-- Edit Button -->
        <button on:click={toggleEditMode} class="absolute top-4 right-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">
            {isEditing ? 'Cancel' : 'Edit'}
        </button>

        <div class="flex items-start space-x-6">
            <!-- Character Image -->
            <div class="w-1/3">
                {#if character.image_url}
                    <img src={`http://localhost:8000${character.image_url}`} alt={character.name} class="rounded-lg w-full h-auto object-cover">
                {:else}
                    <div class="bg-gray-200 rounded-lg w-full h-64 flex items-center justify-center">
                        <span class="text-gray-500">No Image</span>
                    </div>
                {/if}
                {#if isEditing}
                    <div class="mt-2">
                        <label for="imageUpload" class="block text-sm font-medium text-gray-700">Upload new image</label>
                        <input type="file" id="imageUpload" accept="image/*" on:change={handleImageUpload} class="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"/>
                    </div>
                {/if}
            </div>

            <!-- Character Info -->
            <div class="w-2/3">
                {#if isEditing}
                    <input type="text" bind:value={editableName} class="text-3xl font-bold w-full border-b-2 mb-2 p-1">
                    <textarea bind:value={editableDescription} class="text-gray-600 mt-2 w-full border rounded-md p-2" rows="4"></textarea>
                {:else}
                    <h2 class="text-3xl font-bold">{character.name}</h2>
                    <p class="text-gray-600 mt-2">{character.description || 'No description provided.'}</p>
                {/if}

                <div class="mt-4 grid grid-cols-2 gap-4">
                    <div class="bg-gray-100 p-4 rounded-lg">
                        <h4 class="font-bold text-lg">XP</h4>
                        <p class="text-2xl">{character.stats.xp}</p>
                    </div>
                    <div class="bg-gray-100 p-4 rounded-lg">
                        <h4 class="font-bold text-lg">Scrip</h4>
                        <p class="text-2xl">{character.stats.scrip}</p>
                    </div>
                </div>

                {#if isEditing}
                    <button on:click={handleSave} class="mt-4 px-6 py-2 bg-green-500 text-white rounded-md hover:bg-green-600">Save Changes</button>
                {/if}

                {#if error}
                    <p class="text-red-500 mt-2">{error}</p>
                {/if}
                {#if success}
                    <p class="text-green-500 mt-2">{success}</p>
                {/if}
            </div>
        </div>

        <!-- Inventory -->
        <div class="mt-6">
            <h3 class="text-2xl font-bold border-t pt-4">Inventory</h3>
            {#if character.inventory && character.inventory.length > 0}
                <ul class="mt-4 space-y-2">
                    {#each character.inventory as item}
                        <li class="bg-gray-50 p-3 rounded-md flex justify-between">
                            <span>{item.item.name} (x{item.quantity})</span>
                            <span class="text-gray-500 italic">{item.item.description || ''}</span>
                        </li>
                    {/each}
                </ul>
            {:else}
                <p class="mt-4 text-gray-500">Inventory is empty.</p>
            {/if}
        </div>
    </div>
{:else}
    <p>Loading character sheet...</p>
{/if}

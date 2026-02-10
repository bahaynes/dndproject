
import { render } from '@testing-library/svelte';
import { expect, test } from 'vitest';
import MarkdownRenderer from '../lib/components/MarkdownRenderer.svelte';

test('renders markdown correctly', () => {
    const { container } = render(MarkdownRenderer, { content: '# Hello\n**world**' });
    expect(container.innerHTML).toContain('<h1>Hello</h1>');
    expect(container.innerHTML).toContain('<strong>world</strong>');
});

test('sanitizes malicious html', () => {
    const { container } = render(MarkdownRenderer, { content: '<script>alert("xss")</script>**safe**' });
    expect(container.innerHTML).not.toContain('<script>');
    expect(container.innerHTML).toContain('<strong>safe</strong>');
});

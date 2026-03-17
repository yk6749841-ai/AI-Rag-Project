# RTL Hebrew Support - Chef-AI Frontend

## Layout Mirroring Rules
• **Direction Attribute**: `dir="rtl"` on HTML element for Hebrew pages
• **CSS Logical Properties**: Use `margin-inline-start` instead of `margin-left`
• **Flexbox Direction**: `flex-direction: row-reverse` for RTL layouts
• **Grid Positioning**: Reverse column/row order automatically

## Text Alignment & Direction
• **Hebrew Text**: `text-align: right` for all Hebrew content
• **Mixed Content**: `unicode-bidi: plaintext` for proper handling
• **Numbers & Latin**: Keep LTR direction within RTL text
• **Quotes & Punctuation**: Auto-position based on text direction

## Navigation & UI Elements
• **Breadcrumb Arrows**: Point left instead of right in RTL
• **Menu Icons**: Flip hamburger menu to open from right
• **Pagination**: Previous/next buttons swap positions
• **Progress Bars**: Fill from right to left

## Component Adjustments
• **Search Input**: Magnifying glass on right side
• **Dropdown Menus**: Open to the left, not right
• **Modal Dialogs**: Slide in from right side
• **Tool Tips**: Position to the left of trigger element

## Typography Considerations
• **Font Selection**: RTL-optimized fonts like 'Assistant' or 'Rubik'
• **Line Height**: Slightly increased for Hebrew readability
• **Letter Spacing**: Reduced for better Hebrew text flow
• **Text Wrapping**: Proper word breaking for Hebrew words

## Responsive RTL Behavior
• **Mobile First**: RTL rules apply at all breakpoints
• **Touch Gestures**: Swipe gestures reversed for RTL
• **Keyboard Navigation**: Tab order respects RTL layout
• **Focus Management**: Focus rings appear on right side

## CSS Implementation
• **Logical Properties**: Use `margin-inline`, `padding-block`
• **Transforms**: `scaleX(-1)` for icon flipping when needed
• **Writing Mode**: `writing-mode: horizontal-tb` for Hebrew
• **Text Orientation**: `text-orientation: mixed` for mixed content

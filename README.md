# Broken Together
If you can't run it try using the latest version of BlazeSudio by building it from source. Instructions for that are in it's readme.

Credits can be found in CREDITS.md

## How to calculate direction of gravity from a slope
1. Screenshot the slope and find the dimensions of the bounding box of the slope. It doesn't matter if it's zoomed in; we're just finding the gradient. This can be done in many ways;
    - Using a photo editing software like Inkscape to draw a box around the slope and find the dimensions
    - Using a screenshot tool that shows the dimensions (like Flameshot)
    - Screenshot only the slope and find the image dimensions
2. Get out your calculator
3. Plug in `-width/height` into your calculator, where `height` is the height of the bounding box and `width` is the width of the bounding box. This will give you the gradient perpendicular to the slope. **MAKE SURE IF YOUR LINE SLOPES DOWN (`\` as opposed to `/`) YOU USE A NEGATIVE HEIGHT**
4. Find `90-tan⁻¹(gradient)` to get the angle of the slope. This is your gravity. If you're finding it to be upside down, add 180° to the angle.

Or, altogether, `90-tan⁻¹(-width/height)`

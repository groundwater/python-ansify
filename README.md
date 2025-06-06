# Ansify

Python tools for creating ANSI graphics.

- [ ] Fonts
  - [ ] System Fonts -> Img
- [ ] Image
  - [ ] Layer
    - [ ] #raster(x, y)
  - [ ] AffineLayer(transform, layer)
  - [ ] QRCodeLayer(code)
  - [ ] ImageLayer(source)
  - [ ] CropLayer(layer)
  - [ ] FontLayer(text, font, fontSize)
  - [ ] BackgroundLayer(color)
  - [ ] Composite()
    - [ ] .add(layer, mode="")
- [ ] Display
  - [ ] 8-bit
  - [ ] 24-bit

# Development

## Virtual Env


## Dependencies

```
pip install -e .
```

## Update

```
poetry add $DEP
```

# Install

```
git clone $REPO
pip install .
```

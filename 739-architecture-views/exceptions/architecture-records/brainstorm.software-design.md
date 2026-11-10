# brainstorm.software-design does not apply to architecture-records

Both changes follow shapes the package already has, so no structural choice was weighed. The list of required views is a constant beside the code that reads it, and a test checks it against the template, as required-sections-are-wfctls.md already does for spec sections. Record.diagram becomes a list, and the drawing reader looks under one heading per declared kind. The level-2 record already rejected matching drawings by order.

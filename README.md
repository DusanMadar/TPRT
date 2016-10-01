# TPRT - Textured Painted Relief Tool
Purpose of this tool is to create a Textured Painted Relief based on user inputs
and a configuration file; in other words, to automatize the Textured Painted Relief 
generation process. Expected user inputs are preprocessed raster or vector
terrain and landuse layers (ESRI Grid or TIN for terrain; ESRI Grid or ShapeFile
for layers). TPRT was developed as a diploma thesis on Institute of geoinformatics,
VŠB – Technical University of Ostrava, Czech Republic. It is implemented in Python
programming language, based on ArcGIS site package ArcPy. TPRT also uses a XML
configuration file and a XSD schema to validate it. Tool GUI is implemented using
wxPython framework. TPRT can be used from ArcGIS (ArcMap) interface as an
Add-in or outside of the ArcGIS as a standalone script (ArcPy is still necessary though).
Result is a georeferenced raster in *.TIFF | *.JPEG | *.PNG file format, for inspiration
see examples. 

TPR tool is inspired by Jeffery Nighberts (father of the Textured Painted Relief idea)
work and projects. You can find some of the original projects on the following websites: 
- http://proceedings.esri.com/library/userconf/proc98/PROCEED/TO850/PAP842/P842.HTM
- http://proceedings.esri.com/library/userconf/proc03/p0137.pdf
- http://proceedings.esri.com/library/userconf/proc02/pap0400/p0400.htm
- http://blogs.esri.com/Support/blogs/mappingcenter/archive/2010/01/27/A-Concise-History-of-Bump-Mapping.aspx
- http://blogs.esri.com/Support/blogs/mappingcenter/archive/2010/01/25/Symbolizing-the-Bump-Map.aspx

# System requirements
- ArcGIS Desktop 10.1
    - Spatial analyst
    - 3D Analyst
- Python 2.7
    - lxml 2.3.6
    - wxPython 2.8

# TPRT Poster
Poster presenting the project prepared for a student conference.
https://drive.google.com/file/d/0B0VCLmhvZj9maTJycXZEZDJ3R1k/view?usp=sharing (\*.png, 7016 x 9933 pixels, 123 MB)

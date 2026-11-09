# Updating the CV

`Soumitra_Shukla_CV.tex` is the canonical source for the downloadable PDF.
Edit the LaTeX source, then run:

```sh
./build_cv.sh
```

The build requires TeX Live or MacTeX with `latexmk`. It compiles in a temporary
directory, checks for layout and reference warnings, and replaces
`Soumitra_Shukla_CV.pdf` only after a successful build.

Keep the same entries and revision month in `Soumitra_Shukla_CV.html`.
Before publishing, inspect every rendered PDF page and check that all changed
entries and links are present. Commit the source, HTML, and PDF together.
Do not directly rewrite, overlay, compress, stretch, or splice the PDF to edit
its content or typography; make changes in the LaTeX source and rebuild.

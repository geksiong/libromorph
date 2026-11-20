# Music and Fretboards

LibroMorph can illustrate the sound, fingering, and position of an exercise in one chapter. The examples below use [ABC notation]{.index entry="Music!ABC Notation"} for a score, [chord diagrams]{.index entry="Music!Chord Diagrams"} for shapes, and two JavaScript fretboard libraries for scales, exercises, and riffs.

## Sheet Music with ABC

An `abc` block engraves a short melody. Web readers also offer a source toggle; EPUB embeds the score as SVG when an ABC renderer is available.

```abc
X:1
T:Ode to Joy
M:4/4
L:1/4
K:D
F F G A | A G F E | D D E F | F3/2 E/ E2 |
```

## Chord Shapes

Each line of a `chord` block draws one shape. Frets run from the lowest string to the highest; `x` means muted and `0` means open. Finger numbers can reveal barres.

```chord
C    x32010  fingers=x32010
G    320003  fingers=210003
Am   x02210  fingers=x02310
F    133211  fingers=134211
```

## A Calculated Scale with fretboard.js

The `scale` option asks fretboard.js to find every note of A minor pentatonic across the first eight frets. Root notes are highlighted.

```{.fretboard alt="A minor pentatonic notes across the first eight frets"}
{"title":"A minor pentatonic","fretCount":8,
 "scale":{"root":"A","type":"minor pentatonic"}}
```

## A Numbered Exercise with fretboard.js

For a specific path, `dots` places markers by string and fret. Guitar string 6 is the low E; string 1 is the high E. The labels show the order to play these six notes.

```{.fretboard alt="Six-note ascending A minor pentatonic exercise starting on low E"}
{"title":"A minor pentatonic ascent","fretCount":8,
 "dots":[{"string":6,"fret":5,"label":"1"},
         {"string":6,"fret":8,"label":"2"},
         {"string":5,"fret":5,"label":"3"},
         {"string":5,"fret":7,"label":"4"},
         {"string":4,"fret":5,"label":"5"},
         {"string":4,"fret":7,"label":"6"}]}
```

## A Scale Box with Fretdrom

Fretdrom's `scale` diagram specifies a compact fifth-position box. Its grid lists strings from low E to high E, with one entry per fret starting at fret 5. `R` marks A; the other labels are scale degrees.

```{.fretdrom alt="A minor pentatonic scale box at frets five through eight"}
{scale:{name:"A minor pentatonic · fifth position",start_fret:5,num_frets:4,
 grid:[["R", ".", ".", "b3"],
       ["4", ".", "5", "."],
       ["b7",".", "R", "."],
       ["b3",".", "4", "."],
       ["5", ".", ".", "b7"],
       ["R", ".", ".", "b3"]]}}
```

## A Short Riff in Fretdrom Tab

A four-note phrase from that scale can be shown as tab. Tab strings run from high E at the top to low E at the bottom; each character occupies one step.

```{.fretdrom alt="Four-note A minor pentatonic riff in guitar tablature"}
{name:"A minor pentatonic riff",tab:[
  {name:"e",wave:"...."},
  {name:"B",wave:"...."},
  {name:"G",wave:"...."},
  {name:"D",wave:"...."},
  {name:"A",wave:"..57"},
  {name:"E",wave:"58.."}
],config:{bar:4}}
```

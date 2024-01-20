# Notice: As of Krita 5.3, LazyTextTool-Prototype will be discontinued as oncanvas text tool will be included out of box. LazyTextTool was mostly a for fun prototype to see if it could be possible via the python API until a native one was made. Since it has served it's purpose, it has little meaning going forward. You can already play with 5.3 nighlies but be warned not all features may be implemented yet and bugs may exist. But you can still help developers test for issues and make suggestions.

# Krita-LazyTextTool-Prototype
A prototype of a lazily made text tool alternative for Krita (Use at your own risk)
Lazy Text Tool(Prototype) – A plugin that helps you type

Let me say this so everyone is clear, I have never written python before(other than a minor change to an existing plugin). Add to the fact that a lot of this code has been rushed with little to no testing, please keep your expectations in check!



Here is what kinda works

Font:

Typing Text – yes
Colors – yes
Fonts – yes
Font styling – yes


Line and alignment:

Letter spacing – yes
Alignment – yes


Other:

Stroke – yes (same svg 1.1 though)
Canvas scrolling - yes
Moving – yes
Custom fixed width boundary - yes

What partly works:

Canvas zoom – It works, but it is zoom to center, not zoom to mouse
Line spacing – mostly


What doesn’t work:

Gradients – For both color and stroke, it isn’t hard to implement, just needs an interface and be hooked up

Canvas rotation

Word spacing – no

Transforms (rotation/scale) – No, currently, there is no easy way to get transformation/matrix data from svg Text in Krita and storing it is a pain too. That doesn’t mean there is no way. A few options are:
A) Create the text item as a group, then get the data from the group item instead. (but then you won’t be able to edit the text files without ungrouping)

B) Get the data from the KRA file which is effectively a ZIP and stuff it into the id attribute (but this means the file would need to be saved)

C) Get the data via the Copy and retrieve it from there, then store it into the id attribute. (This is probably the most sure fire way to go about it but I think option D is better)

D) Add the things necessary to Krita 5.0 (This is what I am gonna try to do in my free time)

Important Restrictions/Features:

The current setting limits you to only edit layers that have no text object or 1 text object. (so no other shapes, no other text).

When you click the canvas, it will create text typing in Typewriter mode. This is pretty much free typing and is similar to the current text tool. If you draw a box, it will enter into Text Wrap mode. Which pretty much means fixed boundary. You can manually switch modes at any point.

Fixed boundaries are a great thing to play alongside alignment, but the text wrapping is a bit of a hit or miss. It works but it may not render as you think it will based on the platform.

On that note, unlike the normal text tool, this one distinguished between lines and paragraphs.(kinda) When you text wrap or shift+enter, that will make a line. If you just hit enter, that will make a paragraph.(The normal text tool treats everything as a paragraph)

The top left box lets you move the text around while editing, the bottom right box lets you resize the boundary. Do note if you resize the boundary, your lines will be lost(not your paragraphs)

Now this is EXTREMELY important:

This module uses the paste workaround to achieve writing the SVG. Your clipboard will be backed up, then the SVG will be written. Then your clipboard will be restored. That means avoid having something too large in your clipboard if possible when used. And it also means if it crashes before it restores the clipboard, the clipboard will be lost!

When you double click a text item for editing, the vector layer it is on will become invisible. When you commit the change, a new layer is created and the previous layer is deleted.

To commit the changes, left click. To cancel, right click.(outside the text area). If you empty out the text item, it will be deleted with the layer.

Unlike the regular text tool, you can click on text that is outside the current layer. The limit to this is the  current group. If your text is not in any group, that means all layers.

Since the layer is deleted when edited, if you plan to use filters or layer styles, do it on the group, not the layer.

I am probably forgetting a lot of things so I’ll update it later once I remember. But I will say this again cause it needs to be said. The code is a TOTAL mess.

I made this module mostly for my own niche use. I don’t actually even need most of the functions but the curiosity got to me so I rushed most of it to get it out the door. The main goal is to see what the API is missing so it can be expanded hopefully in time for Krita 5.0 (which is a short deadline)

You can expect crashes, memory leaks, poorly written code, hacked in stuff, inconsistent code, rushed code. It is such a big mess, even the debug code is a total mess. This is more of pastebin quality then github quality.

If that sounds good to you, then feel free to try it. To enable, install the plugin via Tools. Then restart Krita. Once restarted, enable it in the configuration and restart again. Then finally, you can toggle it on and off via Tools. It will replace the native text tool.

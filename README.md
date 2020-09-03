# ColorCounter

This program will tally the number of each color present in a picture, by pixel.
Sounds pretty useless right? That's because it is. I only made this project
because I wanted to get a small introduction to openCV. Technically, this
program can work for pictures and videos of any size, but I would highly
recommend only using small pictures, otherwise you'll be waiting for awhile.
The runtime can certainly be improved; if anyone wants to make the program
multithreaded, by my guest. Here is a list of the command line options.

-v, --allowvideos: allow video files to be analyzed as well
-p, --showprogress: show progress bar in the command prompt
-m, --matchcolors: match each rgb pair to the closest named color.
                   Otherwise, colors are counted according to rgb.

If you want to try the program out, the assets folder has a few
small pictures for you to test.
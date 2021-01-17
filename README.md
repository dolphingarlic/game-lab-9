# Lab 9

A tower-defense game about feeding escaped animals in a zoo.

![Demo gif](instructions/lab9.gif)

I got this lab from Laura Li during MISTI-South-Africa 2019, and I recently decided to redo it on a flight to Cape Town!

## Techniques I used

- Rectangle-rectangle intersection.
  - Two rectangles intersect if and only if the sums of their lengths and widths are both smaller than the length and width of their bounding rectangle.
  - This can be checked in O(1) time.
- Ray-polygon intersection.
  - Approach 1 (the one I used):
    - If a ray intersects a polygon, it also intersects at least one of its edges.
    - This means we can reduce this problem to ray-segment intersections.
    - Consider the two vectors V1 and V2 from the origin of the ray to the endpoints of a segment.
    - The ray intersects that segment if and only if the sum of angles between the ray and V1/V2 is equal to the angle between V1 and V2.
      - We can calculate angles using arccos and dot products.
    - This approach works in O(N) time, where N is the number of vertices.
  - Approach 2 (a bit harder to code, but I used this in [IOI 2003 - Seeing the Boundary](https://github.com/dolphingarlic/CompetitiveProgramming/blob/master/IOI/IOI%2003-boundary.cpp), I think):
    - Consider vectors from the origin of the ray to each of the polygon's vertices.
    - The ray is like a vector, so add it to the list of vectors.
    - Sort the list of vectors by angle.
      - We can use cross product to check whether one vector lies counterclockwise to another.
    - The ray intersects the polygon if and only if it's not one of the ends of the sorted list.
    - This approach works in O(N log N) time, but the lack of trigonometric functions make it run a bit faster in practice.
  - Approach 3 (easiest to implement but isn't as exact as the previous two):
    - Consider the minimum enclosing circle and centroid of the polygon.
      - In this lab, all polygons are rectangles, so these are easy to find.
    - The ray "intersects" the polygon if the minimum distance between the centroid and the ray is no greater than the radius of the minimum enclosing circle.
- Moving animals along a path defined by corners only.
  - For each animal, I stored the next corner on its path.
  - If the distance between the animal and that corner is greater than the distance it needs to move, then simply move the animal in that direction by the distance it needs to move.
  - Otherwise,
    - Move the animal to be directly on its next corner and increment that variable.
    - Subtract the distance moved from the distance the animal still needs to move.
    - Distances and displacements can be computed in O(1) time using Pythagoras' theorem.

## Potential extensions

- What if the zookeepers could "auto-aim" like towers in the Bloons Tower Defense series?
- What if the game ramped up in difficulty as it progresses? Right now, one can just buy a few zookeepers and then never lose.
- What if zookeepers can do more than just throw food? For example, a potential zookeeper might slow down animals in their radius.

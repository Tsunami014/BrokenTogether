from BlazeSudio import ldtk
from BlazeSudio.Game import Game
from BlazeSudio import collisions
import BlazeSudio.Game.statics as Ss
from BlazeSudio.utils import approximate_polygon
import pygame

G = Game()
G.load_map("./main.ldtk")

class DebugCommands:
    def __init__(self, Game):
        self.Game = Game
        self.showingColls = False
        self.Game.AddCommand('/colls', 'Toggle collision debug', self.toggleColls)
    
    def toggleColls(self):
        self.showingColls = not self.showingColls
        self.Game.G.Toast(('Showing' if self.showingColls else 'Not showing') + ' collisions')

debug = DebugCommands(G)

def CollProcessor(e):
    if e.identifier == 'CircleRegion':
        return collisions.Circle(e.ScaledPos[0]+e.width/2, e.ScaledPos[1]+e.height/2, e.width/2)
    elif e.identifier == 'RectRegion':
        return collisions.Rect(*e.ScaledPos, e.width, e.height)

class BaseEntity(Ss.BaseEntity):
    def __init__(self, Game, entity):
        super().__init__(Game, entity)
        self.max_speed = 15
    
    def __call__(self, evs):
        objs = collisions.Shapes(*self.Game.currentLvL.GetEntitiesByLayer('GravityFields', CollProcessor))
        oldPos = self.scaled_pos
        thisObj = collisions.Point(*oldPos)
        cpoints = [(i.closestPointTo(thisObj), i) for i in objs]
        if cpoints:
            cpoints.sort(key=lambda x: (thisObj.x-x[0][0])**2+(thisObj.y-x[0][1])**2)
            closest = cpoints[0][0]
            ydiff, xdiff = thisObj.y-closest[1], thisObj.x-closest[0]
            angle = collisions.direction(closest, thisObj)
            tan = cpoints[0][1].tangent(closest, [xdiff, ydiff])
            gravity = collisions.pointOnUnitCircle(angle, -0.2)
        else:
            gravity = [0, 0]
            tan = 0
        self.gravity = gravity
        keys = pygame.key.get_pressed()
        jmp = any(e.type == pygame.KEYDOWN and e.key == pygame.K_UP for e in evs)
        if keys[pygame.K_LEFT] ^ keys[pygame.K_RIGHT] or jmp:
            offs = [(0, 0)]
            if jmp:
                offs.append(collisions.rotateBy0((0, -15), tan-90))
            if keys[pygame.K_LEFT]:
                offs.append(collisions.rotateBy0((-self.acceleration, 0), tan-90))
            elif keys[pygame.K_RIGHT]:
                offs.append(collisions.rotateBy0((self.acceleration, 0), tan-90))
            off = (sum(i[0] for i in offs), sum(i[1] for i in offs))
            self.target_velocity = [self.target_velocity[0] + off[0],
                                    self.target_velocity[1] + off[1]]
        self.apply_physics()
        colls = self.Game.currentScene.collider()
        outRect, self.velocity = thisObj.handleCollisionsVel(self.velocity, colls, False)
        self.pos = self.entity.unscale_pos(outRect)
    
    @property
    def scaled_pos(self):
        return self.entity.scale_pos(self.pos)

@G.DefaultSceneLoader
class MainGameScene(Ss.BaseScene):
    def __init__(self, Game, **settings):
        super().__init__(Game, **settings)
        self.colls = [{}, {}]
        self.sur = None
        self.showingColls = True
        self._collider = None
        self.CamDist = 4
        self.CamBounds = [None, None, None, None]
        for e in self.currentLvl.entities:
            if e.defUid == 6:
                self.entities.append(BaseEntity(Game, e)) # The Player
                self.entities[0].pos = [e.UnscaledPos[0]+0.5, e.UnscaledPos[1]+0.5]
                break
        if self.entities == []:
            raise Ss.IncorrectLevelError(
                'Need a player start!'
            )
    
    @property
    def CamPos(self):
        return self.entities[0].scaled_pos
    
    def collider(self):
        if self._collider is not None:
            return self._collider
        lay = self.Game.currentLvL.layers[1]
        tmpl = ldtk.layer(lay.data, lay.level)
        d = lay.tileset.data.copy()
        d.update({'relPath': d['relPath'] + '/../colls.png'})
        tmpl.tileset = ldtk.Tileset(lay.tileset.fileLoc, d)
        def translate_polygon(poly, translation):
            return collisions.Polygon(*[(i[0]+translation[0], i[1]+translation[1]) for i in poly.toPoints()])
        self._collider = collisions.Shapes(*[translate_polygon(approximate_polygon(t.getImg()), t.pos) for t in tmpl.tiles], *self.Game.currentLvL.GetEntitiesByLayer('Entities', CollProcessor))
        return self._collider

    def render(self):
        if self.sur is not None and debug.showingColls == self.showingColls:
            return self.sur
        self.showingColls = debug.showingColls
        self.sur = self.Game.world.get_pygame(self.lvl)
        if self.showingColls:
            colls = self.collider()
            for col, li in (((255, 10, 50), colls), ((10, 50, 255), self.Game.currentLvL.GetEntitiesByLayer('GravityFields', CollProcessor))):
                for s in li:
                    if isinstance(s, collisions.Polygon):
                        pygame.draw.polygon(self.sur, col, s.toPoints(), 1)
                    if isinstance(s, collisions.Rect):
                        pygame.draw.rect(self.sur, col, (s.x, s.y, s.w, s.h), 1)
                    elif isinstance(s, collisions.Circle):
                        pygame.draw.circle(self.sur, col, (s.x, s.y), s.r, 1)
        return self.sur
    
    def renderUI(self, win, scaleF):
        pos = scaleF(self.entities[0].scaled_pos)
        pygame.draw.circle(win, (0, 0, 0), pos, 10)
        pygame.draw.circle(win, (255, 255, 255), pos, 10, 2)

G.load_scene()

G.play(debug=True)

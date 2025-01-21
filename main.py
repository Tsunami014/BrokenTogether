import math
from BlazeSudio import ldtk, collisions
from BlazeSudio.Game import Game
from BlazeSudio.graphics.GUI import Toast
import BlazeSudio.Game.statics as Ss
from BlazeSudio.utils import approximate_polygon
import pygame

# TODO: Each level inside a level file is all in the one scene, but they are just not loaded if they are not visible

G = Game()
G.set_caption('Broken Together')
G.load_map("./assets/levels/level1/main.ldtk")

class DebugCommands:
    def __init__(self, Game):
        self.Game = Game
        self.showingColls = False
        self.colliding = True
        self.globalMove = False
        self.Game.AddCommand('/colls', 'Toggle collision debug', self.toggleColls)
        self.Game.AddCommand('/ignore', 'Toggle collision ignore', self.toggleIgnore)
        self.Game.AddCommand('/global', 'Toggle global movement', self.toggleGlobal)
    
    def toggleColls(self):
        self.showingColls = not self.showingColls
        G.UILayer.append(Toast(G, ('Showing' if self.showingColls else 'Not showing') + ' collisions'))
    
    def toggleIgnore(self):
        self.colliding = not self.colliding
        G.UILayer.append(Toast(G, ('Applying' if self.colliding else 'Ignoring') + ' collisions'))
    
    def toggleGlobal(self):
        self.globalMove = not self.globalMove
        G.UILayer.append(Toast(G, 'Moving '+('globally' if self.globalMove else 'planet-based')))

debug = DebugCommands(G)

def CollProcessor(e):
    if e.defData['renderMode'] == 'Ellipse':
        return collisions.Circle(e.ScaledPos[0]+e.width/2, e.ScaledPos[1]+e.width/2, e.width/2)
    elif e.defData['renderMode'] == 'Rectangle':
        return collisions.Rect(*e.ScaledPos, e.width, e.height)

class BaseEntity(Ss.BaseEntity):
    def __init__(self, Game, entity):
        super().__init__(Game, entity)
        # Each value is in units per frame unless specified
        self.max_speed = 200  # Max speed
        self.friction = 0.03  # Friction (applied each frame) (in percent of current speed)
        self.not_hold_fric = 0.1 # ADDED friction to apply when not holding ANY KEY (you can modify this to be only left-right or whatever) (in percent of current speed)
        self.not_hold_grav = [0.5, 0.5] # Decrease in gravity to apply when not holding THE UP KEY (in percent of current gravity strength)

        self.movement = 0.5 # How much you move left/right each frame
        self.jump = 150 # Change in velocity when jumping
        self.grav_amount = 0.6 # Gravity strength

        self.gravType = None
        self.gravDir = None
        self.camType = None
        self.camDir = None

    def __call__(self, evs):
        es = self.Game.currentLvL.GetEntitiesByLayer('GravityFields')
        oldPos = self.scaled_pos
        thisObj = collisions.Circle(*oldPos, 2)
        if not debug.globalMove:
            transform = {i: CollProcessor(i) for i in es}
            objs = list(transform.values())
            gravs = [i for i in es if transform[i].collides(thisObj)]
            def findFieldInstance(e, name):
                return [i['__value'] for i in e.fieldInstances if i['__identifier'] == name][0]
            gravs.sort(key=lambda x: (-findFieldInstance(x, 'Layer')))

            self.gravType = None
            self.gravDir = None
            self.camType = None
            self.camDir = None
            invert = None

            for g in gravs:
                if self.gravType is None:
                    self.gravType = findFieldInstance(g, 'GravityType')
                    self.gravDir = findFieldInstance(g, 'GravityDir')
                if self.camType is None:
                    camTyp = findFieldInstance(g, 'Camera')
                    if camTyp == 'Parent':
                        continue
                    self.camType = camTyp
                    self.camDir = findFieldInstance(g, 'CameraDir')
                if invert is None:
                    invert = findFieldInstance(g, 'InvertControls')
            
            if self.gravType is None:
                self.gravType = findFieldInstance(self.entity, 'DefGravityType')
                self.gravDir = findFieldInstance(self.entity, 'GravityDir')
            if self.camType is None:
                self.camType = findFieldInstance(self.entity, 'DefCamera')
                self.camDir = findFieldInstance(self.entity, 'CameraDir')
            if invert is None:
                invert = findFieldInstance(self.entity, 'DefInvertControls')

            cpoints = None
            match self.gravType:
                case 'Global':
                    self.gravity = collisions.pointOnCircle(self.gravDir-90, self.grav_amount)
                    norm = self.gravDir
                case 'Nearest':
                    cpoints = [(i.closestPointTo(thisObj), i) for i in objs]
                case 'NoGrav':
                    self.gravity = [0, 0]
                    norm = math.degrees(collisions.direction((0, 0), self.velocity))-90
                case 'Inwards':
                    collObj = transform[gravs[0]]
                    r = collObj.rect()
                    midp = ((r[2]-r[0])/2+r[0], (r[3]-r[1])/2+r[1])
                    cpoints = [(midp, collisions.Point(*midp))]
                case 'Outwards':
                    collObj = transform[gravs[0]]
                    cpoints = [(collObj.closestPointTo(thisObj), collObj)]
            
            if cpoints is not None:
                cpoints.sort(key=lambda x: (thisObj.x-x[0][0])**2+(thisObj.y-x[0][1])**2)
                closest = cpoints[0][0]
                ydiff, xdiff = thisObj.y-closest[1], thisObj.x-closest[0]
                angle = collisions.direction(closest, thisObj)
                tan = cpoints[0][1].tangent(closest, [-xdiff, -ydiff])
                norm = tan-90
                self.gravity = collisions.pointOnCircle(angle, -self.grav_amount)
            
            if self.gravType == 'Outwards':
                norm += 180
            
            if invert:
                norm += 180

            keys = pygame.key.get_pressed()
            self.holding_jmp = keys[pygame.K_UP]
            self.holding_any = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or self.holding_jmp
            jmp = any(e.type == pygame.KEYDOWN and e.key == pygame.K_UP for e in evs)
            if keys[pygame.K_LEFT] ^ keys[pygame.K_RIGHT] or jmp:
                offs = [(0, 0)]
                if jmp:
                    offs.append(collisions.rotateBy0((0, -15), norm + (180 if invert else 0)))
                if keys[pygame.K_LEFT]:
                    offs.append(collisions.rotateBy0((-self.movement, 0), norm))
                elif keys[pygame.K_RIGHT]:
                    offs.append(collisions.rotateBy0((self.movement, 0), norm))
                off = (sum(i[0] for i in offs), sum(i[1] for i in offs))
                self.velocity = [self.velocity[0] + off[0],
                                  self.velocity[1] + off[1]]
        else:
            self.gravity = [0, 0]
            self.handle_keys()
        self.apply_physics()
        if debug.colliding:
            colls = self.Game.currentScene.collider()
        else:
            colls = collisions.Shapes()
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
        self.off = [0, 0]
        self.lastGrav = None
        self.gravChangeSpeed = 4 # TODO: When we have a player sprite, make the camera go slower than the player's spin animation
        self.CamDist = 4
        self.CamBounds = [None, None, None, None]
        es = self.currentLvl.GetEntitiesByUID(6) # The Player
        if es:
            e = BaseEntity(Game, es[0])
            self.entities.append(e)
            e.pos = [e.entity.UnscaledPos[0]+0.5, e.entity.UnscaledPos[1]+0.5]
        else:
            raise Ss.IncorrectLevelError(
                'Need a player start!'
            )
    
    @property
    def CamPos(self):
        playerPos = self.entities[0].scaled_pos
        return (
            round(playerPos[0]-self.off[0]),
            round(playerPos[1]-self.off[1])
        )
    
    def collider(self):
        if self._collider is not None:
            return self._collider
        colls = []
        for lay in self.Game.currentLvL.layers:
            if lay.identifier == 'GravityFields':
                continue
            if lay.type == 'Tiles':
                tmpl = ldtk.layer(lay.data, lay.level)
                if 'Planets' in lay.identifier:
                    d = lay.tileset.data.copy()
                    d.update({'relPath': d['relPath'] + '/../colls.png'})
                    tmpl.tileset = ldtk.Tileset(lay.tileset.fileLoc, d)
                for t in tmpl.tiles:
                    poly = approximate_polygon(t.getImg())
                    if poly is None:
                        continue
                    colls.append(collisions.ShapeCombiner.pointsToShape(*[(i[0]+t.pos[0], i[1]+t.pos[1]) for i in poly.toPoints()]))
            elif lay.type == 'IntGrid':
                colls.extend(collisions.ShapeCombiner.combineRects(*lay.intgrid.getRects(lay.intgrid.allValues[1:])))
        self._collider = collisions.Shapes(*colls)#, *self.Game.currentLvL.GetAllEntities(CollProcessor))
        return self._collider

    def postProcessGlobal(self, sur):
        return self._Rotate(sur.copy())
    
    def postProcessScreen(self, sur):
        player = self.entities[0]
        camPos = self.CamPos
        diff = (
            camPos[0] - round(player.scaled_pos[0]-self.off[0]),
            camPos[1] - round(player.scaled_pos[1]-self.off[1])
        )
        centre = (self.Game.size[0]/2, self.Game.size[1]/2)
        # Basically, where it should be (in the centre) - where it is (which may change later)
        playerPos = ((centre[0]-diff[0])/self.CamDist, (centre[1]-diff[1])/self.CamDist)

        sze = 16
        playerSur = pygame.Surface((sze, sze), pygame.SRCALPHA)
        pygame.draw.circle(playerSur, (0, 0, 0), (sze/2, sze/2), 7)
        pygame.draw.circle(playerSur, (255, 255, 255), (sze/2, sze/2), 7, 2)
        playerSur = pygame.transform.rotozoom(playerSur, -self.lastGrav%45+22.5, 1) # smooth
        # playerSur = pygame.transform.rotate(playerSur, -self.lastGrav) # pixelated
        sur.blit(playerSur, (playerPos[0]-sze/2, playerPos[1]-sze/2))

        # Debugging scripts
        # sur.blit(pygame.font.Font(None, 30).render(str(playerPos), True, (255, 255, 255)), (0, 0))
        # vel = collisions.rotateBy0(player.velocity, -self.lastGrav)
        # pygame.draw.line(sur, (125, 125, 125), playerPos, (playerPos[0]+vel[0]*10, playerPos[1]+vel[1]*10), 2)

        return sur

    def _Rotate(self, sur):
        match self.entities[0].camType:
            case 'AroundPlayer':
                gravang = math.degrees(collisions.direction((0, 0), self.entities[0].gravity))-90
                gravang = (gravang + self.entities[0].camDir) % 360
            case 'Global':
                gravang = (self.entities[0].camDir) % 360
            case 'AsIs':
                if self.lastGrav is None:
                    self.lastGrav = 0
                gravang = self.lastGrav
    
        if self.lastGrav is None:
            self.lastGrav = gravang
        else:
            angOpts = [gravang, gravang - 360, gravang + 360]
            gravang = min(angOpts, key=lambda x: abs(x - self.lastGrav))
            if self.lastGrav > gravang:
                self.lastGrav -= self.gravChangeSpeed
                if self.lastGrav < gravang:
                    self.lastGrav = gravang
            elif self.lastGrav < gravang:
                self.lastGrav += self.gravChangeSpeed
                if self.lastGrav > gravang:
                    self.lastGrav = gravang
            self.lastGrav %= 360
    
        ang = self.lastGrav
        rotated_sur = pygame.transform.rotozoom(sur, ang, 1)
        old_center = sur.get_rect().center
        rotated_rect = rotated_sur.get_rect()
    
        playerPos = self.entities[0].scaled_pos
        newPos = collisions.rotate(old_center, playerPos, -ang)
        diff = (newPos[0] - playerPos[0], newPos[1] - playerPos[1])
        rotated_rect.center = (old_center[0] - diff[0], old_center[1] - diff[1])
        self.off = rotated_rect.topleft
    
        return rotated_sur

    def render(self):
        if self.sur is not None and debug.showingColls == self.showingColls:
            return self.sur
        self.showingColls = debug.showingColls
        self.sur = self.Game.world.get_pygame(self.lvl, True)
        for e in self.Game.world.get_level(self.lvl).entities:
            if e.layerId.startswith('Entities'):
                self.sur.blit(e.get_tile(), e.ScaledPos)
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

G.load_scene()

G.debug()

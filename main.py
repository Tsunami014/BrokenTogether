import math
import os
from BlazeSudio import ldtk, collisions
from BlazeSudio.Game import Game
from BlazeSudio.graphics import Screen, GUI, options as GO
from BlazeSudio.utils import approximate_polygon
import BlazeSudio.Game.statics as Ss
import pygame

# TODO: Each level inside a level file is all in the one scene, but they are just not loaded if they are not visible

G = Game()
G.set_caption('Broken Together')

# Must be *after* we load the pygame window
from loadWorld import collisionFuncColl  # noqa: E402

def load_level(lvl, *args):
    pth = f"./assets/maps/{lvl}/main.ldtk"
    if not os.path.exists(pth):
        G.UILayer.append(GUI.Toast(G, 'Map does not exist! Use `/maps` to see all the maps', GO.CRED))
        return
    G.load_map(pth)
    if G.currentScene is not None:
        G.load_scene(MainGameScene)

def find_maps():
    return [i for i in os.listdir('./assets/maps') if os.path.isdir(f'./assets/maps/{i}')]

load_level('level1')

class MapScreen(Screen):
    def __init__(self, Game):
        super().__init__()
        self.Game = Game
    
    def __call__(self, *args):
        return super().__call__()
    
    def _LoadUI(self):
        self.layers[0].add('Main')
        LTOP = GO.PNEW((0, 0), (0, 1))
        t = GUI.Text(LTOP, '# Maps:')
        f = GUI.ScrollableFrame(LTOP, (self.size[0], self.size[1]-t.size[1]), (0, 0))
        self['Main'].extend([t, f])
        f.layers[0].add('Main')
        GRID = GO.PNEW((0, 0), (1, 1))
        e = GUI.Empty(GRID, (10, 10))
        g = GUI.GridLayout(GRID)
        f['Main'].extend([e, g])
        rainbow = GO.CRAINBOW()
        def func(lvl):
            load_level(lvl)
            self.Abort()
        btns = [
            GUI.Button(g.LP, next(rainbow), i, func=lambda lvl=i: func(lvl))
            for i in find_maps()
        ]
        cols = math.ceil(math.sqrt(len(btns)))
        g.grid = [
            btns[i*cols:(i+1)*cols] for i in range(cols)
        ]
        f.sizeOfScreen = (max(self.size[0], g.size[0]+20), max(self.size[1]-t.size[1], g.size[1]+20))

class DebugCommands:
    def __init__(self, Game):
        self.Game = Game
        self.showingColls = False
        self.colliding = True
        self.showFPS = False
        self.Game.AddCommand('colls', '/colls ... : Toggle collision debug', self.toggleColls)
        self.Game.AddCommand('ignore', '/ignore ... : Toggle collision ignore', self.toggleIgnore)
        self.Game.AddCommand('fps', '/fps ... : Toggle FPS counter', self.toggleFPS)
        self.Game.AddCommand('load', '/load <name-str> ... : Load a specific map', load_level)
        self.Game.AddCommand('map', '/map ... : Show all the maps', MapScreen(Game))
    
    def toggleColls(self, *args):
        self.showingColls = not self.showingColls
        G.UILayer.append(GUI.Toast(('Showing' if self.showingColls else 'Not showing') + ' collisions'))
    
    def toggleIgnore(self, *args):
        self.colliding = not self.colliding
        G.UILayer.append(GUI.Toast(('Applying' if self.colliding else 'Ignoring') + ' collisions'))
    
    def toggleFPS(self, *args):
        self.showFPS = not self.showFPS
        G.UILayer.append(GUI.Toast(('Showing' if self.showFPS else 'Hiding')+' FPS'))

debug = DebugCommands(G)

def CollProcessor(e):
    if e.defData['renderMode'] == 'Ellipse':
        return collisions.Circle(e.ScaledPos[0]+e.width/2, e.ScaledPos[1]+e.width/2, e.width/2)
    elif e.defData['renderMode'] == 'Rectangle':
        return collisions.Rect(*e.ScaledPos, e.width, e.height)

class BaseEntity(Ss.AdvBaseEntity):
    def __init__(self, Game, entity):
        super().__init__(Game, entity)
        self.canSpin = True
        # Each value is in units per second unless specified
        self.max_speed = 15  # Max speed
        self.max_grav_speed = 15 # Max speed the gravity can get you
        self.friction = 0.8  # Friction perpendicular to or if no grav (applied each frame) (in percent of current speed)
        self.grav_fric = 0.7 # Friction applied in gravity direction (each frame) (in percent of current gravity strength)
        self.not_hold_fric = 0.7 # ADDED friction to apply when not holding ANY KEY (you can modify this to be only left-right or whatever) (in percent of current speed)
        self.not_hold_grav = [0.2, 0.2] # Decrease in gravity to apply when holding THE UP KEY (in percent of current gravity strength)

        self.movement = 1 # How much you move left/right each frame
        self.move_vel = [0, 0]
        self.jump = 9 # Change in velocity when jumping
        self.grav_amount = 15.0 # Gravity strength

        self.hitSize = 24 # Radius of circle hitbox

        self.grav_str = 1
        self.grav_change = 0.08

        self.upforce = 0.05

        # Values set via the fields
        self.grav_adjust = None
        self.gravType = None
        self.gravDir = None
        self.camType = None
        self.camDir = None
        self.camDist = None

    def __call__(self, evs):
        es = self.Game.currentLvL.GetEntitiesByLayer('Fields')
        oldPos = self.scaled_pos
        thisObj = collisions.Circle(*oldPos, self.hitSize)
        transform = {i: CollProcessor(i) for i in es}
        def findFieldInstance(e, name):
            fields = [i['__value'] for i in e.fieldInstances if i['__identifier'] == name]
            return fields[0] if fields else None
        collEs = [i for i in es if transform[i].collides(thisObj)]
        collEs.sort(key=lambda x: (-findFieldInstance(x, 'Layer')))

        if debug.colliding:
            colls = self.Game.currentScene.collider()
        else:
            colls = collisions.Shapes()
        
        for obj in colls:
            obj.bounciness = 0.5

        self.gravType = None
        self.gravDir = None
        self.camType = None
        self.camDir = None
        self.camDist = None
        self.grav_adjust = None
        invert = None

        specifier = None

        for g in collEs:
            if self.gravType is None:
                self.gravType = findFieldInstance(g, 'GravityType')
                specifier = g
            if self.gravDir is None:
                self.gravDir = findFieldInstance(g, 'GravityDir')
            if self.camType is None:
                camTyp = findFieldInstance(g, 'Camera')
                if camTyp == 'Parent':
                    continue
                self.camType = camTyp
            if self.camDir is None:
                self.camDir = findFieldInstance(g, 'CameraDir')
            if self.camDist is None:
                self.camDist = findFieldInstance(g, 'CamDist')
            if self.grav_adjust is None:
                self.grav_adjust = findFieldInstance(g, 'GravityStr')
            if invert is None:
                invert = findFieldInstance(g, 'InvertControls')
        
        if self.gravType is None:
            self.gravType = findFieldInstance(self.entity, 'DefGravityType')
        if self.gravDir is None:
            self.gravDir = findFieldInstance(self.entity, 'DefGravityDir')
        if self.camType is None:
            self.camType = findFieldInstance(self.entity, 'DefCamera')
        if self.camDir is None:
            self.camDir = findFieldInstance(self.entity, 'DefCameraDir')
        if self.camDist is None:
            self.camDist = findFieldInstance(self.entity, 'DefCamDist')
        if self.grav_adjust is None:
            self.grav_adjust = findFieldInstance(self.entity, 'DefGravityStr')
        if invert is None and self.gravType != 'Nearest':
            invert = findFieldInstance(self.entity, 'DefInvertControls')
        
        self.grav_str = min(max(self.grav_adjust, self.grav_str-self.grav_change), self.grav_str+self.grav_change)

        cpoints = None
        match self.gravType:
            case 'Global':
                self.gravity = collisions.pointOnCircle(math.radians(self.gravDir+90), self.grav_amount*self.grav_str)
                norm = self.gravDir
            case 'Nearest':
                cpoints = [(i.closestPointTo(thisObj), i) for e, i in transform.items() if 'Gravity' in e.identifier]
            case 'NoGrav':
                self.gravity = [0, 0]
                norm = math.degrees(collisions.direction((0, 0), self.velocity))-90
            case 'Inwards':
                collObj = transform[specifier]
                r = collObj.rect()
                midp = ((r[2]-r[0])/2+r[0], (r[3]-r[1])/2+r[1])
                cpoints = [(midp, collisions.Point(*midp))]
            case 'Outwards':
                collObj = transform[specifier]
                cpoints = [(collObj.closestPointTo(thisObj), collObj)]
        
        if cpoints is not None:
            cpoints.sort(key=lambda x: (thisObj.x-x[0][0])**2+(thisObj.y-x[0][1])**2)
            closest = cpoints[0][0]
            closestObj = cpoints[0][1]
            if invert is None:
                for obj, coll in transform.items():
                    if coll == closestObj:
                        invert = findFieldInstance(obj, 'InvertControls')
                        break
                else:
                    invert = findFieldInstance(self.entity, 'DefInvertControls')
            ydiff, xdiff = thisObj.y-closest[1], thisObj.x-closest[0]
            angle = collisions.direction(closest, thisObj)
            tan = closestObj.tangent(closest, [-xdiff, -ydiff])
            norm = tan-90
            self.gravity = collisions.pointOnCircle(angle, -self.grav_amount*self.grav_str)
        
        if self.gravType == 'Outwards':
            norm += 180
        
        if invert:
            norm += 180

        keys = pygame.key.get_pressed()
        self.holding_jmp = keys[pygame.K_UP]
        self.holding_any = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or self.holding_jmp
        jmp = any(e.type == pygame.KEYDOWN and e.key == pygame.K_UP for e in evs.copy())
        spin = any(e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE for e in evs) and self.canSpin
        offs = (0, 0)
        if jmp:
            gravdir = collisions.direction((0, 0), self.gravity)
            off = collisions.rotateBy0((self.hitSize*1.5, 0), math.degrees(gravdir))
            if collisions.Line(oldPos, (oldPos[0]+off[0], oldPos[1]+off[1])).collides(colls):
                offs = collisions.rotateBy0((0, -self.jump), norm + (180 if invert else 0))
        if keys[pygame.K_LEFT] ^ keys[pygame.K_RIGHT]:
            if self.movement > 0:
                if keys[pygame.K_LEFT]:
                    side = collisions.rotateBy0((-self.movement, -self.upforce), norm)
                else:
                    side = collisions.rotateBy0((self.movement, -self.upforce), norm)
                self.move_vel[0] += side[0]
                self.move_vel[1] += side[1]
        self.move_vel = [
            min(max(self.move_vel[0] * self.friction, -self.max_speed), self.max_speed),
            min(max(self.move_vel[1] * self.friction, -self.max_speed), self.max_speed)
        ]
        out, self.move_vel, vo = thisObj.handleCollisionsVel(self.move_vel, colls, verbose=True)
        if vo[0]:
            self.canSpin = True
        self.velocity = [self.velocity[0] + offs[0],
                         self.velocity[1] + offs[1]]
        if spin:
            self.canSpin = False
            self.velocity = collisions.rotateBy0((0, -self.jump), norm + (180 if invert else 0))
        self.apply_physics()
        outRect, self.velocity, vo = thisObj.handleCollisionsVel(self.velocity, colls, False, verbose=True)
        if vo[0]:
            self.canSpin = True
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
        self.lastCam = None
        self.playerRot = None
        self.playerSur = pygame.image.load('assets/characters/Ether2.png')
        self.CamDist = 4
        self.CamChangeSpeed = 0.1
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
        return self.off

    def getCloseRect(self):
        player = self.entities[0]
        screenSize = self.Game.size
        diag = math.hypot(*screenSize)/self.CamDist
        radius = max(diag/2, player.max_speed) + 20
        ppos = player.scaled_pos
        return pygame.Rect(ppos[0]-radius, ppos[1]-radius, radius*2, radius*2)
    
    def getScreenRect(self):
        player = self.entities[0]
        screenSize = self.Game.size
        diag = math.hypot(*screenSize)/self.CamDist
        radius = diag/2 + 10
        ppos = player.scaled_pos
        return pygame.Rect(ppos[0]-radius, ppos[1]-radius, radius*2, radius*2)

    # def getClose(self, li, type):
    #     rect = self.getCloseRect()
    
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
                else:
                    for t in tmpl.tiles:
                        poly = collisionFuncColl(tmpl.tileset, *t.src).copy()
                        if collisions.checkShpType(poly, collisions.ShpTyps.NoShape):
                            continue
                        poly.x += t.pos[0]
                        poly.y += t.pos[1]
                        colls.append(poly)
            elif lay.type == 'IntGrid':
                colls.extend(lay.intgrid.getRects(lay.intgrid.allValues[1:]))
        # self.Game.currentLvL.GetAllEntities(CollProcessor)
        self._collider = collisions.ShapeCombiner.combineRects(*colls)
        return self._collider

    def postProcessGlobal(self, sur):
        return self._Rotate(sur)
    
    def postProcessScreen(self, sur, diff):
        screenCentre = self.getScreenRect().center
        playerCentre = self.getCloseRect().center
        diff = (
            screenCentre[0] - playerCentre[0],
            screenCentre[1] - playerCentre[1]
        )
        centre = (self.Game.size[0]/2, self.Game.size[1]/2)
        # Basically, where it is (which may change later) - where it should be (in the centre)
        playerPos = ((centre[0]-diff[0])/self.CamDist, (centre[1]-diff[1])/self.CamDist)

        gravdir = math.degrees(collisions.direction((0, 0), self.entities[0].gravity))-90
        if self.playerRot is None:
            self.playerRot = gravdir % 360
        else:
            angOpts = [gravdir, gravdir - 360, gravdir + 360]
            ncamang = min(angOpts, key=lambda x: abs(x - self.playerRot))
            self.playerRot = (self.playerRot-ncamang)*(9/10)+ncamang
            self.playerRot %= 360
        
        playerSur = pygame.transform.rotozoom(self.playerSur, self.lastCam-self.playerRot, 1) # smooth
        # playerSur = pygame.transform.rotate(self.playerSur, self.playerRot-self.lastCam) # pixelated
        # pygame.draw.circle(playerSur, (0, 0, 0), (sze/2, sze/2), sze/2-1)
        # pygame.draw.circle(playerSur, (255, 255, 255), (sze/2, sze/2), sze/2-1, 2)
        sur.blit(playerSur, (playerPos[0]-playerSur.get_width()/2, playerPos[1]-playerSur.get_height()/2))

        # Debugging scripts
        # sur.blit(pygame.font.Font(None, 30).render(str(self.Game.deltaTime), True, (255, 255, 255)), (0, 30))
        # vel = collisions.rotateBy0(player.velocity, -self.lastGrav)
        # pygame.draw.line(sur, (125, 125, 125), playerPos, (playerPos[0]+vel[0]*10, playerPos[1]+vel[1]*10), 2)
        # off = collisions.rotateBy0((self.entities[0].hitSize*1.5, 0), math.degrees(gravdir)-self.lastCam)
        # pygame.draw.line(sur, (125, 125, 125), playerPos, (playerPos[0]+off[0], playerPos[1]+off[1]), 2)

        # FPS
        if debug.showFPS:
            sur.blit(pygame.font.Font(None, 30).render(f'FPS: {round(self.Game.clock.get_fps(), 3)}', True, (255, 255, 255)), (0, 0))

        return sur

    def _Rotate(self, sur):
        match self.entities[0].camType:
            case 'AroundPlayer':
                camang = math.degrees(collisions.direction((0, 0), self.entities[0].gravity))-90
                camang = (camang + self.entities[0].camDir) % 360
            case 'Global':
                camang = (self.entities[0].camDir) % 360
            case 'AroundClosest':
                thisObj = collisions.Circle(*self.entities[0].scaled_pos, self.entities[0].hitSize)
                d = None
                dir = None
                clo = None
                for e in self.currentLvl.GetEntitiesByLayer('Fields'):
                    if 'Gravity' not in e.identifier:
                        continue
                    p2 = CollProcessor(e).closestPointTo(thisObj)
                    d2 = (thisObj.x-p2[0])**2+(thisObj.y-p2[1])**2
                    if d is None or d2 < d:
                        d = d2
                        dir = [i['__value'] for i in e.fieldInstances if i['__identifier'] == 'CameraDir'][0]
                        clo = p2
                
                if d is None:
                    if self.lastCam is None:
                        self.lastCam = 0
                    camang = self.lastCam
                else:
                    camang = math.degrees(collisions.direction(clo, thisObj))-90
                    camang = (camang + dir + 180) % 360
            case 'AsIs':
                if self.lastCam is None:
                    self.lastCam = 0
                camang = self.lastCam
    
        if self.lastCam is None:
            self.lastCam = camang
        else:
            angOpts = [camang, camang - 360, camang + 360]
            ncamang = min(angOpts, key=lambda x: abs(x - self.lastCam))
            self.lastCam = (self.lastCam-ncamang)*(14/15)+ncamang
            self.lastCam %= 360
    
        rect = self.getCloseRect()
        def constrain(val, sze):
            return min(max(val, 0), sze)
        w, h = rect.size
        x, y = constrain(rect.left, w), constrain(rect.top, h)
        endx, endy = constrain(x+rect.width, sur.get_width()), constrain(y+rect.height, sur.get_height())
        rect2 = pygame.Rect(x, y, endx-x, endy-y)
        cutout = sur.subsurface(rect2)
        new_sur = pygame.Surface((w, h), pygame.SRCALPHA)
        new_sur.blit(cutout, (x-rect.x, y-rect.y))
        rotated_sur = pygame.transform.rotozoom(new_sur, self.lastCam, 1)
        sze = rotated_sur.get_size()
        self.off = (
            sze[0]/2,
            sze[1]/2,
        )

        return rotated_sur

    def render(self):
        nCamDist = self.entities[0].camDist
        if nCamDist:
            self.CamDist = min(max(nCamDist, self.CamDist-self.CamChangeSpeed), self.CamDist+self.CamChangeSpeed)

        if self.sur is not None and debug.showingColls == self.showingColls:
            return self.sur
        self.showingColls = debug.showingColls
        self.sur = self.Game.world.get_pygame(self.lvl, True)
        for e in self.Game.world.get_level(self.lvl).entities:
            if e.layerId.startswith('Entities'):
                self.sur.blit(e.get_tile(), e.ScaledPos)
        if self.showingColls:
            for col, li in (
                    ((255, 10, 50), self.collider()), 
                    ((10, 50, 255), self.Game.currentLvL.GetEntitiesByLayer('Fields', CollProcessor))
                ):
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

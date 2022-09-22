from asyncio.log import logger
from cgitb import enable
import logging
import time

import commands2
import wpilib
from commands2 import InstantCommand, ParallelCommandGroup, ConditionalCommand, SequentialCommandGroup, WaitCommand
from robotpy_toolkit_7407.command import SubsystemCommand
from robotpy_toolkit_7407.motors.ctre_motors import talon_sensor_unit

import config
from oi.keymap import Controllers
from oi.keymap import Keymap
from robot_systems import Robot
from robot_systems import Sensors
from subsystem import Index


class Ball():
    ball_count = 0
    ball = []
    position: str

    def __init__(self, pos):
        self.position = pos

        if pos == "Left":
            Robot.index.left_oc = True
        elif pos == "Right":
            Robot.index.right_oc = True
        elif pos == "Staged":
            Robot.index.staged_oc = True

    team = True
    removed = False
    moving = False

    def isPos(self, pos):
        if pos != "Shot":
            x = pos
            for i in range(len(self.ball)):
                if self.ball[i].position == x:
                    return i
                else:
                   i += 1
            return False
        else:
            i = 0
            self.balls = []
            for i in range(len(self.ball)):
                if self.ball[i].position == "Shot":
                   self.balls.append(i) 
                   i += 1
            return self.balls

    def newPos(self, pos):
        oPos = self.position
        nPos = pos
        if oPos == "Left":
            Robot.index.left_oc = False
            print("Turning off Left OC")
        elif oPos == "Right":
            Robot.index.right_oc = False

        elif oPos == "Staged":
            Robot.index.staged_oc = False

        print("New Position")
        self.position = nPos
        print(self.position)
        if nPos == "Left":
            Robot.index.left_oc = True

        elif nPos == "Right":
            Robot.index.right_oc = True

        elif nPos == "Staged":
            Robot.index.staged_oc = True
    
    def findBalls(self, nPos):
        path_clear = True
        cPos = self.position
        #code break here
        if self.isPos("Left"):
            Robot.index.left_oc = True
        else: ...# testing only remove all of these in production
            #Robot.index.left_oc = False
        if self.isPos("Right"):
            Robot.index.right_oc = True
        else: ...
            #Robot.index.right_oc = False
        if self.isPos("Staged"):
            Robot.index.staged_oc = True
        else: ...
            #Robot.index.staged_oc = False
        
        match nPos:
            case "Left":
                if Robot.index.left_oc != False and cPos != "Left":
                    path_clear = "Left"
                    print("Left Blocked")
                elif Robot.index.staged_oc != False and cPos != "Staged":
                    path_clear = "Stage Block"
                    print("Stage Block Left")
            case "Right":
                if Robot.index.right_oc != False and cPos != "Right":
                    path_clear = "Right"
                    print("Right Blocked")
                elif Robot.index.staged_oc != False and cPos != "Staged":
                    path_clear = "Stage Block"
                    print("Stage Block Right")
            case "Staged":
                if Robot.index.staged_oc != False and cPos != "Staged":
                    path_clear = "Staged"
                    print("Stage Blocked")

        return path_clear

    def disableOC(self, pos):
        match pos:
            case "Left":
                Robot.index.left_oc = False
            case "Right":
                Robot.index.right_oc = False
            case "Staged":
                Robot.index.staged_oc = False
    
    def enableOC(self, pos):
        match pos:
            case "Left":
                Robot.index.left_oc = True
            case "Right":
                Robot.index.right_oc = True
            case "Staged":
                Robot.index.staged_oc = True
    
    def finMove(self, nPos):
        self.disableOC(self.position)
        self.position = nPos
        self.enableOC(self.position)
        self.moving = False

    def __move(self, pos):
        cPos = self.position
        #self.newPos(pos)
        x: object
        y: object
        match pos:
            case "Left":
                print("Dinglebobs Left")
                y = Robot.index.left_limit
                InstantCommand(Robot.index.moveBall("Left", y), Robot.index)
            case "Right":
                print("Dinglebobs Right")
                y = Robot.index.right_limit
                InstantCommand(Robot.index.moveBall("Right", y), Robot.index)
            case "Stage":
                print("Dinglebobs Stage")
                y = Robot.index.photo_electric
                InstantCommand(Robot.index.moveBall("Stage", y, cPos), Robot.index)

    def setPos(self, pos, timeout = 5):
        '''
        Moves the ball based on position

        :Param str pos: the new position for the ball

        :Param int timeout: time for timeout on movement (default 5)

        :Raises TypeError: if pos is not a str

        :Raises ValueError: if pos is not: Left, Right, Stage

        LOGIC:

            If path is not Clear #findBalls uses occupation variables in index subsystem

                turn off dinglebobs
                
                return result
            else:
                set moving variable to pos #too tell program where its going (juggling)

                turn on dinglebobs to move ball
        '''
        nPos = pos
        if self.findBalls(nPos) != True:
            print(self.findBalls(nPos))
            Robot.index.single_dinglebob_off(self.position)
            return self.findBalls(nPos)
        else:
            self.moving = nPos
            self.__move(nPos)

            return True

    def isDone(self, pos):
        '''
        Checks to see if ball movement is finished

        @Param: pos: the movement variable from the ball

            LOGIC:
            
            grabs movement variable output #where the ball is going originally (Match case) 
            and finds motion ending button/photoelectric sensor

            if that value is pressed:
                turn dinglebobs off #probably change after testing

                set position variable too new position

                set moving variable to False

        '''
        y: object
        match pos:
            case "Left":
                print("Dinglebobs not left yet")
                y = Robot.index.left_limit

            case "Right":
                print("Dinglebobs not right yet")
                y = Robot.index.right_limit

            case "Stage":
                y = Robot.index.photo_electric
        if y.get_value():
            print("Limit Reached")
            Robot.index.dinglebobs_off()
            self.newPos(pos)
            self.moving = False
   
    def posNum(oc: str):
        x = 0
        for i in range(len(Ball.ball)):
            if Ball.ball[i].position == oc:
                x = i
            i += 1
        return x
    
    def purge(self):
        if not Robot.index.left_limit.get_value() and not Robot.index.right_limit.get_value() and not Robot.index.photo_electric.get_value():
            Robot.index.dinglebobs_control("Out")

    def remove(self):
        self.removed = True

    def shoot(self):
        x: str
        

class BallPath(SubsystemCommand[Index]):
    def __init__(self, subsystem):
        super().__init__(subsystem)

    def initialize(self) -> None:
        pass

    def execute(self) -> None:
        print("Ball Count")
        print(Ball.ball_count)
        # print("Left:")
        # print(Robot.index.left_oc)
        # print("Right:")
        # print(Robot.index.right_oc)
        #Ball.ball_count = 0 #onlt for testing -- remove when production
        Sensors.color_sensors.multiplexer.writeBulk(bytes([0b0100]))
        left_color = Sensors.color_sensors.color()
        left_val = Sensors.color_sensors.get_val()
        Sensors.color_sensors.multiplexer.writeBulk(bytes([0b1000]))
        right_color = Sensors.color_sensors.color()
        right_val = Sensors.color_sensors.get_val()

        if left_val[0] != 0 and right_val[0] != 0:
            Sensors.color_sensors.working = True
        else:
            Sensors.color_sensors.working = False
            
        if len(Ball.ball) > 0:
            '''
                LOGIC:
                if number of current balls excede 0:
                    search in each ball object:
                        if ball variable moving is not False:
                            check whether the ball is finished moving

            '''
            for i in range(len(Ball.ball)):
                if not Ball.ball[i].removed and Ball.ball[i].moving != False:
                    Ball.ball[i].isDone(Ball.ball[i].moving)
                i += 1

        #print(Robot.index.left_limit.get_value())
        #if Robot.intake.left_intake_down or Robot.intake.right_intake_down:
        if Robot.intake.left_intake_down:
            '''
            Logic:
                If left Intake Down:
                    if left side of index occupied by ball:
                        identify ball number
                        move ball position to right if path clear #no right ball occupation
                    if ball count is not greater than or equal to 2:
                        Run left Dinglebobs #still runs intakes
                    if Left button gets input and no ball occupying left side:
                        get the current ball count
                        create new ball object with left position
                        add 1 to ball count
                        if left color sensor detects not team ball:
                            set ball team to false
                            move ball to stage if path clear #no staged ball occupation
                        else:
                            set ball team to true
                            move ball to right if path clear #no staged ball/no right ball occupation
                else if:
                    turn off left dinglebob

                #Vice versa for right side

            '''
            if Robot.index.left_oc:
                x = Ball.posNum("Left")
                Ball.ball[x].setPos("Right")
            if not Ball.ball_count >= 2:
                Robot.index.single_dinglebob_in("Left")
            if Robot.index.left_limit.get_value() and not Robot.index.left_oc:

                c = Ball.ball_count
                Ball.ball.append(Ball("Left"))
                print("Ball count + 1")
                Ball.ball_count += 1
                #print("Lefty: ", Sensors.color_sensors.get_val())
                #print("Left Color:", left_color)
                Sensors.color_sensors.multiplexer.writeBulk(bytes([0b0100])) #0100 = Left
                #if ball is team ball then store right, if not then stage ball
                if left_color != config.TEAM and left_color != "none":
                    print("OPP BALL")
                    Ball.ball[c].team = False
                    Ball.ball[c].setPos("Stage")
                else:
                    print("TEAM BALL")
                    Ball.ball[c].team = True
                    #if not Robot.index.right_limit.get_value(): #not sure about this. will comment out for now
                    Ball.ball[c].setPos("Right")
                
        elif not Robot.intake.left_intake_down:
            if len(Ball.ball) > 0:
                '''
                    LOGIC:
                    if number of current balls excede 0:
                        search in each ball object:
                            if ball variable moving is not False:
                                check whether the ball is finished moving

                '''
                for i in range(len(Ball.ball)):
                    if not Ball.ball[i].removed and Ball.ball[i].moving != False:
                        Ball.ball[i].isDone(Ball.ball[i].moving)
                    else:
                        Robot.index.single_dinglebob_off("Left")
                    i=+1
            else:
                Robot.index.single_dinglebob_off("Left")

        if Robot.intake.right_intake_down:
            '''
            Logic:
                If left Intake Down:
                    if left side of index occupied by ball:
                        identify ball number
                        move ball position to right if path clear #no right ball occupation
                    if ball count is not greater than or equal to 2:
                        Run left Dinglebobs #still runs intakes
                    if Left button gets input and no ball occupying left side:
                        get the current ball count
                        create new ball object with left position
                        add 1 to ball count
                        if left color sensor detects not team ball:
                            set ball team to false
                            move ball to stage if path clear #no staged ball occupation
                        else:
                            set ball team to true
                            move ball to right if path clear #no staged ball/no right ball occupation
                else if:
                    turn off left dinglebob

                #Vice versa for right side

            '''
            if Robot.index.right_oc:
                x = Ball.posNum("Right")
                Ball.ball[x].setPos("Left")
            if not Ball.ball_count >= 2:
                Robot.index.single_dinglebob_in("Right")
            if Robot.index.right_limit.get_value() and not Robot.index.right_oc:

                c = Ball.ball_count
                Ball.ball.append(Ball("Right"))
                print("Ball count + 1")
                Ball.ball_count += 1
                #print("Lefty: ", Sensors.color_sensors.get_val())
                #print("Left Color:", left_color)
                Sensors.color_sensors.multiplexer.writeBulk(bytes([0b0100])) #0100 = Left
                #if ball is team ball then store right, if not then stage ball
                if right_color != config.TEAM and right_color != "none":
                    print("OPP BALL")
                    Ball.ball[c].team = False
                    Ball.ball[c].setPos("Stage")
                else:
                    print("TEAM BALL")
                    Ball.ball[c].team = True
                    #if not Robot.index.right_limit.get_value(): #not sure about this. will comment out for now
                    Ball.ball[c].setPos("Left")
                
        elif not Robot.intake.right_intake_down:
            if len(Ball.ball) > 0:
                '''
                    LOGIC:
                    if number of current balls excede 0:
                        search in each ball object:
                            if ball variable moving is not False:
                                check whether the ball is finished moving

                '''
                for i in range(len(Ball.ball)):
                    if not Ball.ball[i].removed and Ball.ball[i].moving != False:
                        Ball.ball[i].isDone(Ball.ball[i].moving)
                    else:
                        Robot.index.single_dinglebob_off("Right")
                    i=+1
            else:
                Robot.index.single_dinglebob_off("Right")

                
            #Robot.intake.dinglebobs_in()
            #Robot.index.left_dinglebob.set_raw_output(-.7)
        #else: 
            #...#Robot.index.dinglebobs_off()

        # logging.info(f"Color Sensors {left_val, right_val}")

        

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool) -> None:
        pass

class stage():

    def initialize(self) -> None:
        pass

    def execute(self) -> None:

        if Robot.index.staged_oc:
            y: str
            x = Ball.posNum("Staged")
            if Ball.ball[x].team == False:
                if Robot.index.left_oc:
                    y = "Left"
                if Robot.index.right_oc:
                    y = "Right"
                Ball.ball[x].setPos(y)
            else:
                Ball.ball[x].shoot()
        else:
            x = 0
            if Robot.intake.left_intake_down:
                x = Ball.posNum("Left")
                if x:
                    Ball.ball[x].setPos("Stage")
                else:
                    x = Ball.posNum("Right")
                    if x:
                        Ball.ball[x].setPos("Stage")
            if Robot.intake.right_intake_down:
                x = Ball.posNum("Right")
                if x:
                    Ball.ball[x].setPos("Stage")
                else:
                    x = Ball.posNum("Left")
                    if x:
                        Ball.ball[x].setPos("Stage")

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool) -> None:
        pass

class destage():

    def initialize(self) -> None:
        pass

    def execute(self) -> None:

        if Robot.index.staged_oc:
            y: str
            x = Ball.posNum("Staged")
            if Robot.index.left_oc:
                y = "Left"
            if Robot.index.right_oc:
                y = "Right"
            Ball.ball[x].setPos(y)
        # else:
        #     x = 0
        #     if Robot.intake.left_intake_down:
        #         x = Ball.posNum("Left")
        #         if x:
        #             Ball.ball[x].setPos("Stage")
        #         else:
        #             x = Ball.posNum("Right")
        #             if x:
        #                 Ball.ball[x].setPos("Stage")
        #     if Robot.intake.right_intake_down:
        #         x = Ball.posNum("Right")
        #         if x:
        #             Ball.ball[x].setPos("Stage")
        #         else:
        #             x = Ball.posNum("Left")
        #             if x:
        #                 Ball.ball[x].setPos("Stage")

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool) -> None:
        pass
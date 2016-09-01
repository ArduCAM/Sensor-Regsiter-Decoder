import datetime
import time
import csv

## IMAGE SENSOR REGISTER PROGRAMMING DISASSEMBLER
## OV2640Program.loadRegisters()
## OV2640Program.printRegisters()
## programs = ['OV2640_QVGA','OV2640_JPEG_INIT','OV2640_YUV422','OV2640_JPEG','OV2640_160x120_JPEG','OV2640_176x144_JPEG',
##             'OV2640_320x240_JPEG','OV2640_352x288_JPEG','OV2640_640x480_JPEG','OV2640_800x600_JPEG',
##             'OV2640_1024x768_JPEG','OV2640_1280x1024_JPEG','OV2640_1600x1200_JPEG']
## for aProgram in programs :
##     progFile = open(aProgram + ".regpgm.cpp", "w")
##     pgm = OV2640Program();
##     pgm.describe(aProgram,"H",progFile)
##     pgm.describe(aProgram,"L",progFile)
##     pgm.describe(aProgram,"M",progFile)
##     progFile.close()
class OV2640BitField :
    def __init__(self,name,value,desc):
        self.name = name.strip()
        self.value = value.strip()
        self.description = desc.strip()
        self.isVariable = None
        self.isParsed = False
    def hasDescription(self) :
        return self.description != None and len(self.description) > 0
    # return description or name
    def getDescription(self) :
        if self.hasDescription() :
            return self.description
        return self.name
    # return the field in a non-compilable descriptive form
    # format H)igh level, L)ow level, M)achine level
    def printField(self,decodedArg,fieldFormat) :
        if fieldFormat == "H" :
            if self.isSimpleFlag() :
                desc = '{:s}'.format(self.getDescription())
            else:
                desc = '{:s}({:d})'.format(self.getDescription(),decodedArg)
        elif fieldFormat == "L" :
            if self.isSimpleFlag() :
                desc = '{:s}'.format(self.name)
            else:
                desc = '{:s}({:d})'.format(self.name,decodedArg)
        else:
            desc = ''
            
        return desc

    #true for constant flags
    def isSimpleFlag(self) :
        return self.isVariable == False
    # returns the flag value
    def simpleFlagValue(self,progArg) :
        if ((progArg & self.value == self.value and self.value > 0) or
            (progArg == 0 and self.value == 0)):
            return self.value
        return None
    # true if the bit field is set
    def isBitField(self) :
        return self.isVariable == True
    # get the bit field value AND mask it out
    def extractBitFieldValue(self,progArg) :
        shiftmask = self.value[1] << self.value[2]
        bits = progArg & shiftmask
        downshift = self.getRegisterShift()
        bits = bits >> downshift
        bits = bits & self.value[1]
        bits << self.value[0]
        #mask the field out of the arg
        progArg = progArg & (~shiftmask)
        return [bits,progArg]
    def getRegisterShift(self):
        if self.isVariable != True:
            return None
        return self.value[2]
    def compile(self):
        if self.isParsed == False and self.value.startswith('0x'):
            self.value = int(self.value,16)
            self.isVariable = False
            self.isParsed = True
        elif self.isParsed == False and self.value.startswith('[') :
            ss = self.value[1:-1]
            ss = ss.split(',')
            ss[0] = int(ss[0],10)
            ss[1] = int(ss[1],16)
            ss[2] = int(ss[2],10)
            self.value = ss
            self.isVariable = True
class OV2640Register:
    'Defines a register on the )V2640 Sensor Array'
    reserveCounters = [0,0]
    def __init__(self,bank,name,subscript,datatype,defaultValue,address,mitTag,bitFields) :
        self.bank = bank
        if name == 'RSVD':
            c = OV2640Register.reserveCounters[self.bank]
            name = '{:s}{:02d}'.format(name,c)
            c += 1
            OV2640Register.reserveCounters[self.bank] = c
        
        self.name = name
        self.subscript = subscript
        self.datatype = datatype
        self.defaultValue = defaultValue
        self.address = address
        self.mitTag = mitTag
        self.bitFields = bitFields
    def hasDescription(self) :
        return self.mitTag != None and len(self.mitTag) > 0
    def registerName(self) :
        return 'RB{:d}_{:s}'.format(self.bank,self.name)
    
    def registerDeclaration(self) :
        return 'const uint8_t {:s} = 0x{:02x};'.format(self.registerName(),self.address)
    def cantDecodeArgument(self,progArg) :
        return '0x{:02x}'.format(progArg)
    # this will example a register value and attempt to decode it - it
    # will return any bitfields and flags it identifies and the remaining
    # bits that were not processed
    def decodeArgument(self,progArg):
        selectedFields = []      
        # if no bitfield definitions then it can't be decoded
        if(len(self.bitFields) == 0):
            return [selectedFields,progArg]
        
        # iterate over the bit fields
        for aBitField in self.bitFields :
            if aBitField.isSimpleFlag() :
                flagValue = aBitField.simpleFlagValue(progArg)
                if flagValue != None :
                    selectedFields.append([aBitField,flagValue])
                # mask the field out of the arg
                progArg = progArg & (~aBitField.value)
            elif aBitField.isBitField() :
                fieldVal,newProgArg = aBitField.extractBitFieldValue(progArg)
                selectedFields.append([aBitField,fieldVal])
                #mask the field out of the arg
                progArg = newProgArg
        return [selectedFields,progArg]
                                       
    
    def printArgument(self,decodeVector,fieldFormat) :
        summary = ''
        for decodeItem in decodeVector :
            bitField,fieldValue = decodeItem
            if len(summary) > 0:
                summary += " | "
            dtext = bitField.printField(fieldValue,fieldFormat)
            desc = ' {:s} '.format(dtext)
            summary = summary + desc
        return summary
class OV2640Program:
    'Defines an ordered set of register loads for the OV2640 image sensor'
    registerSet0 = [None] * 256
    registerSet1 = [None] * 256
    @staticmethod
    def loadRegisters():
        OV2640Register.reserveCounters[0] = 0
        OV2640Register.reserveCounters[1] = 0
        firstRow = True
        with open("Register Map1.csv") as f:
            reader = csv.reader(f)
            for row in reader:
                if firstRow :
                    firstRow = False
                    continue
                address = row[0].strip()
                bank = int(row[1].strip(),10)
                name = row[2].strip()
                subscript = row[3].strip()
                default = row[4].strip()
                direction = row[5].strip()
                mitTag = ''
                bitfields = []
                optCount = len(row)
                if optCount > 6:
                    mitTag = row[6]
                    fieldIndex = 7
                    while fieldIndex < optCount and len(row[fieldIndex]) > 0:
                        bf = OV2640BitField(row[fieldIndex],row[fieldIndex + 1],row[fieldIndex + 2]);
                        bf.compile()
                        bitfields.append(bf)
                        fieldIndex += 3
                dashIndex = address.find("-")
                if dashIndex != -1 :
                    min = int(address[:dashIndex].strip(),16)
                    max = int(address[1+dashIndex:].strip(),16)
                else:
                    min = int(address,16)
                    max = min

                bracketIndex = name.find("[")
                datatype = "WORD"
                if bracketIndex != -1 :
                    bracket = name[bracketIndex:].strip()
                    datatype = types.get(bracket, bracket)
                    name = name[:bracketIndex]
                    
                for regAddr in range(min,max+1):
                    register = OV2640Register(bank,name,subscript,datatype,default,regAddr,mitTag,bitfields)
                    if bank == 0:
                        OV2640Program.registerSet0[regAddr] = register
                    else:
                        OV2640Program.registerSet1[regAddr] = register
    @staticmethod
    def printRegisters():
        for i in range(0,256):
            if OV2640Program.registerSet0[i] != None:
                print(OV2640Program.registerSet0[i].registerDeclaration())
        for i in range(0,256):
            if OV2640Program.registerSet1[i] != None:
                print(OV2640Program.registerSet1[i].registerDeclaration())
    def __init__(self) :
        self.program = []
        self.activeBank = None
        
    def describe(self,programName,fieldFormat,progFile) :
        if fieldFormat != "M" :
            print("/********************************************",file=progFile)
            print("START Program,{:s}\t\tGenerated,{:s}\t\tLevel:{:s}".format(programName,time.strftime("%c"),fieldFormat),file=progFile)
            print(file=progFile)
        else:
            print("const struct sensor_reg {:s}[] =".format(programName),file=progFile)
            print("{",file=progFile)
        fileName = programName + '.csv'
        with open(fileName) as f:
            reader = csv.reader(f)
            self.activeBank = 1
            lineCtr = 1
            for row in reader:
                if len(row) == 2 :
                    regAddr = int(row[0].strip(),16)
                    regValue = int(row[1].strip(),16)
                    assert regAddr != 255 or regValue != 255
                    self.program.append([regAddr,regValue])
                    if fieldFormat != "M":
                        progtext = self.printLine(regAddr,regValue,fieldFormat,lineCtr)
                    else:
                        progtext = "\t{:s}0x{:02x},0x{:02x}{:s},\t\t//{:03d}".format("{",regAddr,regValue,"}",lineCtr)
                    print(progtext,file=progFile)
                    lineCtr += 1
            if fieldFormat != "M" :     
                print(file=progFile)
                print("END Program,{:s}\t\tGenerated,{:s}\t\tLevel:{:s}".format(programName,time.strftime("%c"),fieldFormat),file=progFile)
                print("********************************************/",file=progFile)
            else:
                print("};",file=progFile)
                print(file=progFile)
    def printLine(self,regAddr,regValue,fieldFormat,lineCtr) :
        if regAddr == 255:
            self.activeBank = regValue
            register = OV2640Program.registerSet0[255]
        elif self.activeBank == 0:
            register = OV2640Program.registerSet0[regAddr]
        elif self.activeBank == 1:
            register = OV2640Program.registerSet1[regAddr]
        else:
            opCode = '0x{:02x}'.format(regAddr)
        if self.activeBank != None and fieldFormat != "M" :
            if fieldFormat == "H" and register.hasDescription() :
                printReg = register.mitTag
            else: 
                printReg = register.registerName();
            if(printReg == None or len(printReg) == 0) :
                printReg = '0x{:02x}'.format(regAddr)
            decodedFields,remainingbits = register.decodeArgument(regValue)
            if len(decodedFields) > 0 :
                printVal = register.printArgument(decodedFields,fieldFormat)
                if remainingbits > 0 :
                    unknownBits = ' ??{:02x}?? '.format(remainingbits)
                    printVal = printVal + unknownBits
            else:
                printVal = '0x{:02x}'.format(regValue)
        else:
            printReg = '0x{:02x}'.format(regAddr)
            printVal = '0x{:02x}'.format(regValue)
        return "{:03d}\t\t{:s}\t{:s}".format(lineCtr,printReg.ljust(40),printVal)



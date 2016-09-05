# Sensor-Regsiter-Decoder
Decoder the binary form of sensor register settings into human readable format developed by Mark Mullin.

This is a tool for decoding the programming for the image sensor modules used by the Arducam.  The current work focuses on the OV2640 sensor, however, other sensors can be added by defining the spreadsheet that defines the registers and enables the tool to reproduce the program for that sensor in a more easily understood form.  One of the clearest developments already with this tool is the fact that a large number of critical registers are totally undocumented.

 In order for us as a community to learn what all these registers do, these spreadsheets provide a way to gather together what we know of the registers and their individual functions.  In doing this, the more advanced capabilities of the sensors with respect to gain control, image collection time, and pan and zoom functions will be more easily used by all of us.

If you are experimenting with sensor settings and you determine details of how specific registers work, and those registers aren’t documented, please submit your updates to the spreadsheets so that we all can benefit from what you have learned.  In this way, we as a community can help each other with this basic understanding of the sensors and their programming registers.

The decoder application is based on a python script that reads in a spreadsheet documenting what is known about the registers and then rewriting the standard sensor program using this information, such that this
const struct sensor_reg OV2640_JPEG_INIT[] =

{

{0xff,0x00},	//001

{0x2c,0xff},	//002

{0x2e,0xdf},	//003

{0xff,0x01},	//004

{0x3c,0x32},	//005

{0x11,0x04},	//006

{0x09,0x02},	//007

{0x04,0x28},	//008

{0x13,0xe5},	//009

{0x14,0x48},	//010

{0x2c,0x0c},	//011

…

becomes (for C++)
/********************************************
START Program,OV2640_JPEG_INIT		Generated,Sun Sep  4 16:08:21 2016		Level:C++
********************************************/

const struct sensor_reg OV2640_JPEG_INIT[] =
{
	{RB0_RA_DLMT,0x00},                              /*1	[ff := 00]		Register Bank Select	 DSP(00)/DSP */
	{RB0_RSVD_2c,0xff},                              /*2	[2c := ff]		RB0_RSVD_2c	0xff*/
	{RB0_RSVD_2e,0xdf},                              /*3	[2e := df]		RB0_RSVD_2e	0xdf*/
	{RB0_RA_DLMT,0x01},                              /*4	[ff := 01]		Register Bank Select	 SENS(01)/SENS */
	{RB1_RSVD_3c,0x32},                              /*5	[3c := 32]		RB1_RSVD_3c	0x32*/
	{RB1_CLKRC,0x04},                                /*6	[11 := 04]		Internal clock	0x04*/
	{RB1_COM2,0x02},                                 /*7	[09 := 02]		Common control 2	0x02*/
	{RB1_REG04,0x28},                                /*8	[04 := 28]		Register 04	 Always set/DEF  |  HREF_EN(08)/HREF_EN */
	{RB1_COM8,0xe5},                                 /*9	[13 := e5]		Common control 8	 Banding filter1/DEF  |  Banding filter2/BNDF_EN  |  AGC Auto/Manual/AGC_EN  |  Auto/Manual Exposure/AEC_EN */
	{RB1_COM9,0x48},                                 /*10	[14 := 48]		Common control 9 Automatic gain ceiling - maximum AGC value [7:5]	 AGC_GAIN_8x(40)/AGC_GAIN_8x  ??08?? */
	{RB1_RSVD_2c,0x0c},                              /*11	[2c := 0c]		RB1_RSVD_2c	0x0c*/
	{RB1_RSVD_33,0x78},                              /*12	[33 := 78]		RB1_RSVD_33	0x78*/
	{RB1_RSVD_3a,0x33},                              /*13	[3a := 33]		RB1_RSVD_3a	0x33*/
	{RB1_RSVD_3b,0xfb},                              /*14	[3b := fb]		RB1_RSVD_3b	0xfb*/
...
};


and becomes (for JSON)

{
	"pgm" : [
	["0xff","0x00","001   Register Bank Select =  DSP(00)/DSP "],
	["0x2c","0xff","002   RB0_RSVD_2c = 0xff"],
	["0x2e","0xdf","003   RB0_RSVD_2e = 0xdf"],
	["0xff","0x01","004   Register Bank Select =  SENS(01)/SENS "],
	["0x3c","0x32","005   RB1_RSVD_3c = 0x32"],
	["0x11","0x04","006   Internal clock = 0x04"],
	["0x09","0x02","007   Common control 2 = 0x02"],
	["0x04","0x28","008   Register 04 =  Always set/DEF  |  HREF_EN(08)/HREF_EN "],
	["0x13","0xe5","009   Common control 8 =  Banding filter1/DEF  |  Banding filter2/BNDF_EN  |  AGC Auto/Manual/AGC_EN  |  Auto/Manual Exposure/AEC_EN "],
	["0x14","0x48","010   Common control 9 Automatic gain ceiling - maximum AGC value [7:5] =  AGC_GAIN_8x(40)/AGC_GAIN_8x  ??08?? "],
	["0x2c","0x0c","011   RB1_RSVD_2c = 0x0c"],
	["0x33","0x78","012   RB1_RSVD_33 = 0x78"],
	["0x3a","0x33","013   RB1_RSVD_3a = 0x33"],
	["0x3b","0xfb","014   RB1_RSVD_3b = 0xfb"],
	...
	]
}




The spreadsheet contains a number of columns, arranged like this
A -  Hex register address or range of addresses
B - Register bank (0 == DSP, 1 == Sensor)
C- Short meaningful name for register to use in disassembly
D - Subscript - an apparent bit range attached to registers in documentation
E - Default register value from documentation
F - register data direction(s)
G- Note taken from MIT driver implementation

the following columns are a repeating 3 element tuple describing individual bit fields and flags in the register

1 - Name of bit field
2 - constant flag value for bit flags, or [left shift, bit mask, right shift] for multibit variables
3 - description of bit field

The information that is in the spreadsheet now is taken from the OV2640 document from Omnivision and a driver implementation available here -  (https://stuff.mit.edu/afs/sipb/contrib/linux/drivers/media/i2c/soc_camera/ov2640.c)    There is more useful information in the OV2640 application note that can be added to the spreadsheet, and we hope that efforts by the larger community can help identify and decode other registers, so that we can continue to learn how the sensor is programmed through it’s registers.

The sensor program files themselves were extracted from the Arducam reference implementation and have each been placed in individual files.

If you have discovered details about other registers, or want to decode other sensors such as the OV5642, please submit pull requests to github so we can keep updating this information and share it with the larger community.  This is a much more efficient way for us all to learn the mysteries of the reserved undocumented registers.


Files in this release

Register Map.ipynb	     — Jupyter python 3 notebook with the register decoding program -- if you don't have Anaconda and Jupyter, you're really missing out on a cool tool - go here http://jupyter.readthedocs.io/en/latest/install.html
Register Map.csv         -   Current disassembly information used by Python notebook
OV2640*.csv		     -  Raw register programs from Arducam reference implementation, consumed by disassembler


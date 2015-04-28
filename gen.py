#!/usr/bin/python

# Generate an HTML file representing a Kerbal Space Program science checklist
# Created by Tyler Bletsch -- discspace.org
# Modified for KSP 1.0 by Dimitri "Tyrope" Molenaars -- tyrope.nl


import sys,os,re

##################################################
##### UTILITY FUNCTIONS
##################################################

# Parse a tab-delimited string into a 2D array
# (The result of pasting in from Excel is a tab-separated array, so this is a lazy way to import data while still having the code be readable)
def parse_table(table_tsv, xform=None):
    table_rows = table_tsv.strip().split("\n")

    table = {}

    col_headers = table_rows[0].split("\t")[1:]
    row_headers = [x.split("\t")[0] for x in table_rows[1:]]
    for row_header,row in zip(row_headers,table_rows[1:]):
        values = row.split("\t")[1:]
        table[row_header] = {}
        for (col_header,value) in zip(col_headers,values):
            if xform: value = xform(value)
            table[row_header][col_header] = value
    return (row_headers,col_headers,table)

# format numbers with non-trivial fractional components like ###.#, numbers close to integers get shown as integers
def fmt(v):
    if v-int(v)>0.05:
        return "%.1f" % v
    else:
        return "%d" % v

##################################################
##### RAW DATA
##### (Data-munging code in here is just doing some transformation to make lookups easier later, and is safe to ignore.
##################################################

#Known bug: Splashed and Landed aren't modeled seperately,
# causing inaccuracies across several planets and biomes.
biomes = {
    'Bop': ["Peaks","Poles","Ridges","Slopes","Valley"],
    'Dres': ["Canyons","Highlands","Impact Craters","Impact Ejecta","Lowlands",
        "Midlands","Poles","Ridges"],
    'Duna': ["Craters","Highlands","Lowlands","Midlands","Poles"],
    'Eeloo': ["Craters","Glaciers","Highlands","Ice Canyons","Lowlands",
        "Midlands","Poles"],
    'Eve': ["Explodium Sea","Highlands","Impact Ejecta","Lowlands","Midlands",
        "Peaks","Poles"],
    'Gilly': ["Highlands","Lowlands","Midlands"],
    'Ike': ["Central Mountain Range","Eastern Mountain Ridge","Lowlands",
        "Midlands","Polar Lowlands","South Eastern Mountain Range","South Pole",
        "Western Mountain Ridge"],
    'Jool': ['&nbsp;'], #Jool has no biomes. :(
    'Kerbin': ["Administration","Astronaut Complex","Badlands","Crawlerway",
        "Deserts","Flag Pole","Grasslands","Highlands","Ice Caps","KSC",
        "LaunchPad","Mission Control","Mountains","R&D","R&D Central Building",
        "R&D Corner Lab","R&D Main Building","R&D Observatory","R&D Side Lab",
        "R&D Small Lab","R&D Tanks","R&D Wind Tunnel","Runway","Shores","SPH",
        "SPH Main Building (Roof)","SPH Round Tank","SPH Tanks",
        "SPH Water Tower","Tracking Station","Tracking Station Dish East",
        "Tracking Station Dish North","Tracking Station Dish South",
        "Tracking Station Hub","Tundra","VAB","VAB Main Building (Roof)",
        "VAB Pod Memorial","VAB Round Tank","VAB Tanks","Water"],
    'Laythe': ["Cresent Bay","Dunes","Poles","Shores","The Sagen Sea"],
    'Minmus': ["Flats","Greater Flats","Great Flats","Highlands","Lesser Flats",
        "Lowlands","Midlands","Poles","Slopes"],
    'Moho': ["Canyon","Central Lowlands","Highlands","Midlands",
        "Minor Craters","Northern Sinkhole","Northern Sinkhole Ridge",
        "North Pole","South Eastern Lowlands","South Pole",
        "South Western Lowlands","Western Lowlands"],
    'Mun': ["Canyons","East Crater","East Farside Crater","Farside Crater",
        "Highland Craters","Highlands","Midland Craters","Midlands",
        "Northern Basin","Northwest Crater","Polar Crater","Polar Lowlands",
        "Poles","Southwest Crater","Twin Craters"],
    'Pol': ["Highlands","Lowlands","Midlands","Poles"],
    'Kerbol': ['&nbsp;'], # Kerbol has no biomes. :(
    'Tylo': [
        # Tylo having 3 "Major Crater" biomes is NOT a bug!
        "Highlands","Lowlands","Major Crater","Major Crater","Major Crater",
        "Mara","Midlands","Minor Craters"],
    'Vall': ["Highlands","Lowlands","Midlands","Poles"]
}

page_break_before_planets = ['Kerbin','Mun','Minmus','Laythe']
moons = ["Gilly","Mun","Minmus","Ike","Laythe","Vall","Tylo","Bop","Pol"]

atmosphere_havers = set("Kerbin Eve Duna Jool Laythe".split())

no_surface = set("Kerbol Jool".split())

zone_test_to_scope_table_tsv = """
x	Surf	EVA	Crew	Goo	Matl	Temp	Baro	Grav	Seis	Nose	Recover
Surface	Biome	Biome	Biome	Biome	Biome	Biome	Biome	Biome	Biome	Biome	Multizonal
FlyLow	-	Biome	Biome	Global	Global	Biome	Global	-	-	Biome	Multizonal
FlyHigh	-	Global	Global	Global	Global	Global	Global	-	-	Biome	Multizonal
SpaceLow	-	Biome	Global	Global	Global	Global	-	Biome	-	-	Multizonal
SpaceHigh	-	Global	Global	Global	Global	-	-	Biome	-	-	Multizonal
"""

(zones,tests,zone_test_to_scope) = parse_table(zone_test_to_scope_table_tsv)

base_points = {
    'Surf': 30,
    'EVA': 8,
    'Crew': 5,
    'Goo': 10,
    'Matl': 25,
    'Temp': 8,
    'Baro': 12,
    'Grav': 20,
    'Seis': 20,
    'Nose': 20,
    'Recover': -1,
}

transmit_rate = {
    'Surf': 25,
    'EVA': 100,
    'Crew': 100,
    'Goo': 30,
    'Matl': 20,
    'Temp': 50,
    'Baro': 50,
    'Grav': 40,
    'Seis': 45,
    'Nose': 35,
    'Recover': -1,
}

lab_transmit_bonus = {
    'Surf': 12,
    'EVA': 0,
    'Crew': 0,
    'Goo': 15,
    'Matl': 10,
    'Temp': 25,
    'Baro': 25,
    'Grav': 20,
    'Seis': 22,
    'Nose': 17,
    'Recover': -1,
}

planet_mzone_to_multiplier_table_tsv = """
x	Surface	Fly	Space
Kerbol	-1	-1	11
Moho	9	-1	8
Eve	12	7	7
Gilly	9	-1	8
Kerbin	0.3	0.7	1
Mun	4	-1	3
Minmus	5	-1	4
Duna	8	7	7
Ike	9	-1	8
Dres	8	-1	7
Jool	-1	7	7
Laythe	10	9	9
Vall	10	-1	9
Tylo	11	-1	10
Bop	9	-1	8
Pol	9	-1	8
Eeloo	9	-1	8
"""

(_, mzones, planet_mzone_to_multiplier) = parse_table(planet_mzone_to_multiplier_table_tsv, xform=float)

zone2mzone = {
    'Surface':'Surface',
    'FlyHigh':'Fly',
    'FlyLow':'Fly',
    'SpaceHigh':'Space',
    'SpaceLow':'Space',
}

# Algorithm to get the value of a given experiment. 
# BUG: The 'Recover' test is known to be wrong.
def get_values(planet,mzone,test):
    if test=='Recover':
        return {
            'recover':5,
            'base': 5,
            'multiplier': 1,
        }
    base = base_points[test]
    multiplier = planet_mzone_to_multiplier[planet][mzone]
    value = base*multiplier
    value_transmit = value * transmit_rate[test]/100.0
    value_transmit_lab = value * (transmit_rate[test] + lab_transmit_bonus[test]) / 100.0
    return {
        'recover':value,
        'transmit':value_transmit,
        'transmit_lab':value_transmit_lab,
        'base': base,
        'multiplier': multiplier
    }

# which experiments cant be done in water?
no_water_tests = set(['Seis','Nose'])

# which experiments need at atmosphere to work?
need_atmosphere_tests = set(['Baro','Nose'])

if 0: #DEBUG switch
    print tests
    print zones
    print zone_test_to_scope
    print "--"
    print mzones
    print _
    print planet_mzone_to_multiplier
    print zone2mzone
    sys.exit(1)

#NOTE no water for nose/seis surface
#NOTE recovery from section (need to glob Fly* and Space*)

##################################################
##### HTML HEADER STUFF
##################################################

print """
<html>
<Head>
<style>
    body {
        font-family: "Trebuchet MS", Helvetica, sans-serif;
        font-size: 12pt;
    }

    div.header {
        text-align: center;
    }

    div.footer {
        margin-top: 48px;
        text-align: center;
        color: #888;
        font-size:80%;
    }

    table {
        border-collapse: collapse;
        border: none;
    }

    tr.newpage {
        page-break-before: always;
    }

    td.null {
        background-color: #fff;
        border: none;
    }

    th.row {
        text-align: left;
        border-top: 1px solid #aaa;
        border-left: none;
        border-right: none;
        border-bottom: 1px solid #aaa;
    }

    th.planet {
        text-align: center;
    }

    td,th {
        padding: 2px;
        border: 1px solid #aaa;
        background-color: #e4e4e4;
    }
    th.test {
        width:3em;
        vertical-align: bottom;
    }
    td.valid {
        background-color: #fff;
        border: 1px solid #888;
        ztext-align: center;
        vertical-align: top;
        font-size: 70%;
        color: #aaa;
    }
    td.invalid {
        background-color: #888;
        border: 1px solid #888;
    }
    thead {display: table-header-group;}

</style>
</head>
<body>
<div class=header>
    <img src="img/logo.png" width=300><BR>
    <H1>Science Checklist</h1>
    Revision 3 &mdash; KSP version 1.0 &mdash; 2015 April 27.
    <P>
</div>
"""

print "<table border=1>"
print "<thead>"
print "<tr><Td colspan=3 class=null>"
for test in tests:
    print "<th class=test>"
    print "<img src='img/tests/%s.png' width=48><BR>" % test
    print "%s" % test
print "</thead><tbody>"

##################################################
##### TABLE GENERATION
# The really sinful part - this started as a simple "iterate and print" loop, 
# but I kept having to add conditions to match the reality of KSP. Things like 
# "you need an atmosphere to be flying", "you can't land on planets with no surface", 
# etc. There's also a bunch of conditionals for formatting things like HTML pagebreaks. 
# The nastiest thing is scope, which can be "-", "--", or "---" depending on how "scopeless" 
# it is...this makes no sense and is a strong indicator of brain damage on my part. Your 
# best bet are the little comments on the conditional checks for that. Another horrible 
# part is the insane math and logic around the row-spanning cells, since that screws 
# up the nice orderly table logic.
##################################################


for planet in biomes.iterkeys():
    num_planet_rows = 5
    has_atmosphere = planet in atmosphere_havers

    applicable_zones = [z for z in zones if has_atmosphere or not z.startswith('Fly')]
    num_zones = len(applicable_zones)

    applicable_biomes = biomes[planet]
    num_biomes = len(applicable_biomes)

    for i_zone,zone in enumerate(applicable_zones):
        mzone = zone2mzone[zone]
        if mzone=='Fly' and not has_atmosphere: continue

        for i_biome,biome in enumerate(applicable_biomes):
            c = ''
            if i_zone==0 and i_biome==0 and planet in page_break_before_planets:
                c='newpage'
            print "<tr class='%s'>" % c

            if i_zone==0 and i_biome==0: # planet label
                print "<th class='row planet' rowspan=%d>" % (num_zones*num_biomes)
                w=64
                if planet in moons: w=32
                if planet=='Kerbol': w=96
                print "<img src='img/planets/%s.png' width=%d><BR>" % (planet,w)
                print "%s" % planet

            if i_biome==0: # zone label
                print "<th class=row rowspan=%d>%s" % (num_biomes,zone)

            print "<th class=row>%s" % biome.replace(' ','&nbsp;')

            for test in tests:
                scope = zone_test_to_scope[zone][test]
                if planet in no_surface and zone=='Surface': scope='--'
                if zone=='Surface' and biome=='Water' and test in no_water_tests: scope='--'
                if not has_atmosphere and test in need_atmosphere_tests: scope='---'
                if planet=='Kerbin' and zone=='Surface' and test=='Recover': scope='-'
                if scope=='-': # no to all biomes in this zone
                    if i_biome==0:
                        print "<td class=invalid rowspan=%d>" % num_biomes
                elif scope=='--': # no to this zone/biome pair (one row)
                    print "<td class=invalid>"
                elif scope=='---': # no to this whole planet
                    if i_zone==0 and i_biome==0:
                        print "<td class=invalid rowspan=%d>" % (num_biomes*num_zones)
                elif scope=='Biome':
                    values = get_values(planet,mzone,test)
                    s = '<BR>'.join("%s=%.1f"%(k,v) for (k,v) in values.items())
                    #print "<td style='background-color:#FF8;'>%.1f<BR>%.1f<BR>%.1f" % (values['recover'], values['transmit'], values['transmit_lab'])
                    print "<td class=valid>%s" % (fmt(values['recover']))
                    #print "<td style='background-color:#FF8;'>%s" % s
                elif scope=='Global':
                    if i_biome==0:
                        values = get_values(planet,mzone,test)
                        #s = '<BR>'.join("%s=%.1f"%(k,v) for (k,v) in values.items())
                        print "<td class=valid rowspan=%d>%s" % (num_biomes,fmt(values['recover']))
                        #print "<td style='background-color:#FFa;' rowspan=%d>%s" % (num_biomes,s)
                elif scope=='Multizonal':
                    values = get_values(planet,mzone,test)
                    if (zone=='FlyLow' or zone=='SpaceLow') and i_biome==0:
                        print "<td class=valid rowspan=%d>%s" % (2*num_biomes,fmt(values['recover']))
                    if (zone=='Surface') and i_biome==0:
                        print "<td class=valid rowspan=%d>%s" % (num_biomes,fmt(values['recover']))
print "</tbody>"
print "</table>"

print """
<div class=footer>
Created by Tyler Bletsch &mdash; <a href="http://discspace.org/">discspace.org</a><br />
Modified for 1.0 by Dimitri Molenaars &mdash; <a href="http://tyrope.nl/">tyrope.nl</a>
</div>
</body></html>

"""

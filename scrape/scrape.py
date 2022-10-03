from typing import Optional, Sequence
from bs4 import BeautifulSoup
import os
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar


class FileType(Enum):
    CONSTANTS = 1
    CLASS = 2


#### ADT 1 for parsing


@dataclass
class Arg:
    name: str
    tp: str


@dataclass
class Property:
    name: str
    tp: str


@dataclass
class Ctor:
    args: Sequence[Arg]


@dataclass
class Method:
    args: Sequence[Arg]
    retval: str
    name: str


@dataclass
class ThreeFile:
    name: str
    fileType: FileType
    path: str
    extends: Optional[str] = None
    ctor: Optional[Ctor] = None
    properties: Optional[Sequence[Property]] = None
    methods: Optional[Sequence[Method]] = None


@dataclass
class XArg:
    name: str
    tp: None


@dataclass
class XCtor:
    args: Sequence[XArg]


@dataclass
class ThreeClass:
    name: str
    path: str
    extends: Optional[str] = None
    ctor: Optional[XCtor] = None
    # properties: Optional[Sequence[XProperty]] = None
    # methods: Optional[Sequence[XMethod]] = None


FILES = []

SOURCE = {}


def fixParam(f, t, n, p):
    return (
        "String"
        if p == "string"
        else "Number"
        if p == "number"
        else "Number"
        if p == "Radians"
        else "TextureFormat"
        if (p == "Constant") and (f == "FramebufferTexture")
        else "Material"
        if p == "material"
        else "Material"
        if p == "Material"
        else "BufferAttributeUsage"
        if p == "Usage"
        else p
        if "/" not in p
        else p.split("/")[-1].split(".")[0]
    )


for root, dirs, files in os.walk("./three.js/src", topdown=False):
    for fi in files:
        fullPath = os.path.join(root, fi)
        if fullPath[-3:] == ".js":
            SOURCE[fi[:-3]] = fullPath

for root, dirs, files in os.walk("./three.js/docs/api/en", topdown=False):
    for fi in files:
        if fi[-5:] == ".html":
            fullPath = os.path.join(root, fi)
            with open(fullPath, "r") as infi:
                soup = BeautifulSoup(infi.read(), "html.parser")
                h1s = [h1 for h1 in soup.find_all("h1")]
                if len(h1s) != 1:
                    raise ValueError(f"{fullPath} has too-long header")
                headerString = h1s[0].string
                threeFile = ThreeFile(
                    name=fi[:-5] if headerString == "[name]" else h1s[0].string,
                    fileType=FileType.CLASS
                    if headerString == "[name]"
                    else FileType.CONSTANTS,
                    path=fullPath,
                )
                ### We look up the file in the actual source to see if it extends something
                if threeFile.name in SOURCE:
                    with open(SOURCE[threeFile.name]) as src:
                        lines = src.read().split("\n")
                        done = False
                        extends = None
                        i = 0
                        while (not done) and (i < len(lines)):
                            x = lines[i]
                            if ("class " in x) and (" extends " in x):
                                x = x.split(" ")
                                for r in range(len(x)):
                                    if x[r] == "extends":
                                        extends = x[r + 1]
                                        done = True
                                        break
                            i += 1
                        threeFile.extends = extends

                ### Skip PropertyBinding for now as there's too much undocumented stuff, come back to it later
                if "PropertyBinding" == threeFile.name:
                    continue
                ### Skip PropertyMixer for now as there's too much undocumented stuff in PropertyBinding, come back to it later
                if "PropertyMixer" == threeFile.name:
                    continue
                ### Skip GLBufferAttribute for now, come back to it later
                if "GLBufferAttribute" == threeFile.name:
                    continue
                ### AnimationUtils has some undocumente types, so skip it for now
                if threeFile.name in ["AnimationUtils"]:
                    continue
                ### ShapeUtils has some undocumente types, so skip it for now
                if threeFile.name in ["ShapeUtils"]:
                    continue
                ### Earcut has some undocumente types, so skip it for now
                if threeFile.name in ["Earcut"]:
                    continue
                ### Skip the audio stuff
                ### it'd be nice to have it eventually, but I don't need it,
                ### so it's one less headache for now
                if "Audio" in threeFile.name:
                    continue
                h2s = [h2 for h2 in soup.find_all("h2") if h2.string == "Constructor"]
                if len(h2s) == 1:
                    ctorH2 = h2s[0]
                    ctorH3 = ctorH2
                    while True:
                        ctorH3 = ctorH3.next_sibling
                        if ctorH3.name == "h3":
                            ### CubeTexture and Texture have a documented constructor but
                            ### it shouldn't be exposed and it's not typed
                            if threeFile.name in ["CubeTexture", "Texture"]:
                                break
                            ### DataTexture has some undocumented types, so skip it for now
                            if threeFile.name in ["DataTexture"]:
                                break
                            ### SpotLightShadow takes an empty constructor
                            params = (
                                []
                                if threeFile.name == "SpotLightShadow"
                                else [
                                    [
                                        i
                                        for i in param.replace("param:", "").split(" ")
                                        if i != ""
                                    ]
                                    for param in ctorH3.string.split("(")[1]
                                    .split(")")[0]
                                    .split(",")
                                ]
                            )
                            if params == [[]]:
                                params = []
                            ### DataArrayTexture does not have types,
                            ### so we add them here
                            if threeFile.name == "DataArrayTexture":
                                params = [["Number", param[0]] for param in params]
                            ### PropertyBinding has number parameters if they do not have
                            ### an explicit type
                            if threeFile.name == "PropertyBinding":
                                params = [
                                    ["Number", param[0]] if len(param) == 1 else param
                                    for param in params
                                ]
                            ### AnimationObjectGroup has a variable number of objects in the ctor
                            ### we represent that using an array
                            if threeFile.name == "AnimationObjectGroup":
                                params = [["Array", "objects"]]
                            ### LinearInterpolant, DiscreteInterpolant, QuaternionLinearInterpolant, CubicInterpolant are not documented, so hardcode it
                            if threeFile.name in [
                                "LinearInterpolant",
                                "QuaternionLinearInterpolant",
                                "DiscreteInterpolant",
                                "CubicInterpolant",
                            ]:
                                params = [
                                    ["Float32Array", "parameterPositions"],
                                    ["Float32Array", "sampleValues"],
                                    ["Integer", "sampleSize"],
                                    ["Float32Array", "resultBuffer"],
                                ]
                            params = [
                                [
                                    item.replace(" ", "")
                                    .replace("[", "")
                                    .replace("]", "")
                                    for item in param
                                ]
                                for param in params
                            ]
                            params = [
                                Arg(
                                    param[1],
                                    fixParam(
                                        threeFile.name, "CTOR", param[1], param[0]
                                    ),
                                )
                                for param in params
                            ]
                            threeFile.ctor = Ctor(params)
                            break
                h2s = [h2 for h2 in soup.find_all("h2") if h2.string == "Properties"]
                if len(h2s) == 1:
                    properties = []
                    ctorH2 = h2s[0]
                    ctorH3 = ctorH2
                    while True:
                        ctorH3 = ctorH3.next_sibling
                        if ctorH3.name == "h3":
                            if ctorH3.string[:4] == "See ":
                                continue
                            property = (
                                ctorH3.string.replace("[property:", "")
                                .replace("]", "")
                                .split(" ")
                            )
                            property = Property(
                                property[1],
                                fixParam(
                                    threeFile.name, "PROPERTY", property[1], property[0]
                                ),
                            )
                            properties.append(property)
                        if ctorH3.name == "h2":
                            break
                    threeFile.properties = properties
                h2s = [h2 for h2 in soup.find_all("h2") if h2.string == "Methods"]
                if len(h2s) == 1:
                    methods = []
                    ctorH2 = h2s[0]
                    ctorH3 = ctorH2
                    while True:
                        ctorH3 = ctorH3.next_sibling
                        if ctorH3 is None:
                            break
                        if ctorH3.name == "h3":
                            toParse = (
                                str(ctorH3)
                                .replace("<h3>", "")
                                .replace("</h3>", "")
                                .replace("\n", " ")
                                .replace("<br/>", "")
                            )
                            if toParse[:4] == "See ":
                                continue
                            toParse = toParse.replace("[method:", "")
                            toParse = toParse.split(" ")
                            retval = fixParam(
                                threeFile.name, "RETVAL", None, toParse[0]
                            )
                            toParse = " ".join(toParse[1:])
                            toParse = toParse.split("]")
                            methodName = toParse[0].replace(" ", "")
                            toParse = "]".join(toParse[1:])
                            toParse = (
                                toParse.replace("(", "")
                                .replace(")", "")
                                .replace("[", "")
                                .replace("]", "")
                                .split(",")
                            )
                            params = [
                                [
                                    i
                                    for i in param.replace("param:", "").split(" ")
                                    if i != ""
                                ]
                                for param in toParse
                            ]
                            if params == [[]]:
                                params = []
                            params = [
                                [
                                    item.replace(" ", "")
                                    .replace("[", "")
                                    .replace("]", "")
                                    for item in param
                                ]
                                for param in params
                            ]
                            ### PropertyBinding has number parameters if they do not have
                            ### an explicit type
                            if (threeFile.name == "PropertyBinding") and (
                                methodName == "Composite"
                            ):
                                params = [
                                    ["Number", param[0]] if len(param) == 1 else param
                                    for param in params
                                ]
                            ### BufferArray lacks a type in the documentation
                            params = (
                                [Arg("array", "Array")]
                                if (threeFile.name == "BufferAttribute")
                                and (methodName == "copyArray")
                                else [Arg("objects", "Array")]
                                if (threeFile.name == "Object3D")
                                and (methodName == "add")
                                else [Arg("buffer", "Buffer")]
                                if (threeFile.name == "GLBufferAttribute")
                                and (methodName == "setBuffer")
                                else [Arg("objects", "Array")]
                                if (threeFile.name == "Object3D")
                                and (methodName == "remove")
                                else [Arg("meta", "Object")]
                                if (threeFile.name == "LOD")
                                and (methodName == "toJSON")
                                else [Arg("objects", "Array")]
                                if (threeFile.name == "AnimationObjectGroup")
                                and (methodName == "add")
                                else [Arg("objects", "Array")]
                                if (threeFile.name == "AnimationObjectGroup")
                                and (methodName == "remove")
                                else [Arg("objects", "Array")]
                                if (threeFile.name == "AnimationObjectGroup")
                                and (methodName == "uncache")
                                else [
                                    Arg(
                                        param[1],
                                        fixParam(
                                            threeFile.name,
                                            methodName,
                                            param[1],
                                            param[0],
                                        ),
                                    )
                                    for param in params
                                ]
                            )
                            method = Method(name=methodName, retval=retval, args=params)
                            methods.append(method)
                        if ctorH3.name == "h2":
                            break
                    threeFile.methods = methods
                FILES.append(threeFile)

TYPES = set()

def massageArg(arg):
    return (
        arg.tp
        if arg.tp != "Function"
        else arg.name[0].upper() + arg.name[1:] + "Function"
    )


CHECKING = "Constant"


for fi in FILES:
    if fi.ctor is not None:
        for arg in fi.ctor.args:
            TYPES.add(massageArg(arg))
            if arg.tp == CHECKING:
                print(fi.name,'ctor', arg)
    if fi.properties is not None:
        for prop in fi.properties:
            TYPES.add(massageArg(prop))
            if arg.tp == CHECKING:
                print(fi.name, fi, prop)
    if fi.methods is not None:
        for method in fi.methods:
            TYPES.add(method.retval)
            if method.retval == CHECKING:
                print(fi.name, 'retval', method)
            for arg in method.args:
                TYPES.add(massageArg(arg))
                if arg.tp == CHECKING:
                    print(fi.name, 'prop', arg)

FILENAMES = set()
for fi in FILES:
    FILENAMES.add(fi.name)
# print(' | '.join('X'+tp for tp in TYPES))

######
### Code to help identify tricky types
for tp in TYPES:
    if (
        (tp not in FILENAMES)
        and ("_" not in tp)
        and (tp != "undefined")
        and (tp != "this")
        and (tp != "Array")
        and (tp != "Object")
        and (tp != "String")
        and (tp != "Boolean")
        and (tp != "Integer")
        and (tp != "Hex")
        and (tp != "Number")
        and (tp != "Float")
        and (tp != "Any")
        and (tp != "Promise")  # so far, always a unit promise in three API
        and (not ((tp[-8:] == "Function") and (tp != "Function")))
        and (
            tp != "Vector"
        )  # if a funciton has vector as an argument, then it works either for Vector2 or for Vector3, and the API on top of it should have two functions for both vector types
        and (
            tp != "TypedArray"
        )  # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/TypedArray
        and (
            tp != "WebGL2RenderingContext"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/WebGL2RenderingContext
        and (
            tp != "WebGLContextAttributes"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/WebGLRenderingContext/getContextAttributes
        and (
            tp != "JSON"
        )  # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON
        and (
            tp != "Float32Array"
        )  # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Float32Array
        and (
            tp != "XRSession"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/XRSession
        and (
            tp != "XRReferenceSpace"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/XRReferenceSpace
        and (
            tp != "HTMLImageElement"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement
        and (
            tp != "HTMLElement"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement
        and (
            tp != "HTMLCanvasElement"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement
        and (
            tp != "Video"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement
        and (
            tp != "BufferAttributeUsage"
        )  # https://threejs.org/docs/?q=BufferAttribute#api/en/constants/BufferAttributeUsage
        and (
            tp != "TextureFormat"
        )  # https://threejs.org/docs/?q=CubeTexture#api/en/constants/Textures (Formats)
        and (
            tp != "RenderTarget"
        )  # https://threehttps://threejs.org/docs/?q=RenderTar#api/en/renderers/WebGLRenderTarget etc
    ):
        raise ValueError(tp)
######

deferred = []

with open("types.py", "w") as outfi:
    outfi.write(
        """from typing import Optional, Sequence
from bs4 import BeautifulSoup
import os
from dataclasses import dataclass
from enum import Enum

"""
    )
    outfi.write(
        f"""@dataclass
class XUnion:
    left: 'XType'
    right: 'XType'
"""
    )
    for tp in TYPES:
        if tp == "Array_or_Integer":
            deferred.append(
                "Array_or_Integer = XUnion(left=XArray(val=XInteger()), right=XInteger())\n"
            )
        elif tp == "Color_Hex_or_String":
            deferred.append(
                "Color_Hex_or_String = XUnion(left=XColor(), right=XUnion(left=XHex(), right=XString()))\n"
            )
        elif tp in ["Array", "Object"]:
            outfi.write(
                f"""@dataclass
class X{tp}:
    val: 'XType'
"""
            )
        else:
            outfi.write(
                f"""@dataclass
class X{tp}: pass
"""
            )
    for line in deferred:
        outfi.write(line)
    outfi.write(
        "XType = "
        + (" | ".join(["X" + tp for tp in TYPES if "_" not in tp] + ["XUnion"]))
    )

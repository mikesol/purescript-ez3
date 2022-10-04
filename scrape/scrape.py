from typing import Optional, Sequence
from bs4 import BeautifulSoup
import os
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar


class FileType(Enum):
    CONSTANTS = 1
    CLASS = 2


@dataclass
class OptionalArg:
    val: "ArgTp"


@dataclass
class ArrayArg:
    val: "ArgTp"


@dataclass
class MutableArrayArg:
    val: "ArgTp"


@dataclass
class ObjectArg:
    vals: Sequence["ArgTp"]


@dataclass
class RecordArg:
    val: "ArgTp"


@dataclass
class UnionArg:
    left: "ArgTp"
    right: "ArgTp"


ArgTp = (
    str | ArrayArg | RecordArg | MutableArrayArg | ObjectArg | OptionalArg | UnionArg
)

#### ADT 1 for parsing


@dataclass
class Constant:
    name: str
    constants: Sequence[str]


@dataclass
class Arg:
    name: str
    tp: ArgTp


@dataclass
class Property:
    name: str
    tp: ArgTp


@dataclass
class Ctor:
    args: Sequence[Arg]


@dataclass
class Method:
    args: Sequence[Arg]
    retval: ArgTp
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
    constants: Optional[Sequence[Constant]] = None


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
        else "Hex"
        if p == "hex"
        else "HTMLElement"
        if p == "DOMElement"
        else "BlendingMode"
        if p == "Blending"
        else "Number"
        if p == "number"
        else "Number"
        if p == "Radians"
        else "FormatConstant"
        if (p == "Constant") and (f == "FramebufferTexture")
        else "EncodingConstant"
        if (p == "Constant") and (f == "MeshDepthMaterial")
        else "ToneMappingConstant"
        if (p == "Constant") and (f == "WebGLRenderer")
        else "InterpolationModeConstant"
        if (p == "Constant")
        and (
            f == "KeyframeTrack"
            or f == "BooleanKeyframeTrack"
            or f == "StringKeyframeTrack"
            or f == "QuaternionKeyframeTrack"
        )  # more nuanced needed?
        else "TypeConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "type")
        else "MappingModeConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "mapping")
        else "WrappingModeConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "wrapS")
        else "WrappingModeConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "wrapT")
        else "MagnificationFilterConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "magFilter")
        else "MinificationFilterConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "minFilter")
        else "FormatConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "format")
        else "Material"
        if p == "material"
        else "Material"
        if p == "Material"
        else "GeometryUsageConstant"
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
                if threeFile.fileType == FileType.CONSTANTS:
                    ## we use a special parser
                    constants = []
                    curElt = soup.find_all("h2")[0]
                    curName = None
                    while True:
                        curElt = curElt.next_sibling
                        if curElt is None:
                            break
                        if curElt.name == "h2":
                            curName = curElt.string
                        if curElt.name == "code":
                            consts = [
                                y
                                for y in [
                                    x.replace("THREE.", "")
                                    .replace(" ", "")
                                    .replace("\t", "")
                                    for x in curElt.string.split("\n")
                                ]
                                if y != ""
                            ]
                            if curName is not None:
                                constants.append(
                                    Constant(
                                        name=curName.replace(" ", "") + "Constant",
                                        constants=consts,
                                    )
                                )
                    threeFile.constants = constants
                    FILES.append(threeFile)
                    continue
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
                            # internal, so skip
                            # https://threejs.org/docs/?q=WebGLRenderer#api/en/renderers/WebGLRenderer.renderLists
                            if (property[1] == "renderLists") and (
                                property[0] == "WebGLRenderLists"
                            ):
                                continue
                            # Shadow maps are objects, so fill this in later
                            if property[1] == "shadowMap":
                                property[0] = "Object"
                            if property[1] == ".generateMipmaps":
                                property[1] = "generateMipmaps"
                            if property[1] == "generateMipmaps":
                                property[0] = "Boolean"
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


CHECKING = "???"
TEXTURE_PROPS = {}
for fi in FILES:
    if fi.ctor is not None:
        for arg in fi.ctor.args:
            arg = massageArg(arg)
            TYPES.add(arg)
            if arg == CHECKING:
                print(fi.name, "ctor", arg)
    if fi.properties is not None:
        for prop_ in fi.properties:
            if "[" in prop_.tp and "Texture" in prop_.tp:
                prop_.tp = TEXTURE_PROPS[prop_.name]
            prop = massageArg(prop_)
            if fi.name == "Texture":
                TEXTURE_PROPS[prop_.name] = prop
            TYPES.add(prop)
            if prop == CHECKING:
                print(fi.name, prop, prop_)
    if fi.methods is not None:
        for method in fi.methods:
            TYPES.add(method.retval)
            if method.retval == CHECKING:
                print(fi.name, "retval", method)
            for arg in method.args:
                arg = massageArg(arg)
                TYPES.add(arg)
                if arg == CHECKING:
                    print(fi.name, "prop", arg)

FILENAMES = set()
for fi in FILES:
    FILENAMES.add(fi.name)
# print(' | '.join('X'+tp for tp in TYPES))

######
### Code to help identify tricky types
for tp in sorted(TYPES):
    if (
        (tp not in FILENAMES)
        and ("_" not in tp)
        and (tp != "undefined")
        and (tp != "this")
        and (tp != "Array")
        and (tp != "Object")
        and (tp != "String")
        and (tp != "Boolean")
        and (tp != "null")
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
            tp != "WebGLShader"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/WebGLShader
        and (
            tp != "Shader"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/WebGLShader
        and (
            tp != "TypedArray"
        )  # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/TypedArray
        and (
            tp != "Image"
        )  # https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/Image
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
            tp != "GeometryUsageConstant"
        )  # https://threejs.org/docs/?q=BufferAttribute#api/en/constants/GeometryUsageConstant
        and (
            tp != "FormatConstant"
        )  # https://threejs.org/docs/?q=CubeTexture#api/en/constants/Textures (Formats)
        and (
            tp != "RenderTarget"
        )  # https://threehttps://threejs.org/docs/?q=RenderTar#api/en/renderers/WebGLRenderTarget etc
        and (
            tp != "BlendingMode"
        )  # https://threejs.org/docs/?q=Materials#api/en/constants/Materials
        and (
            tp != "ToneMappingConstant"
        )  # https://threejs.org/docs/?q=WebGLRenderer#api/en/constants/Renderer
        and (
            tp != "TypeConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
        and (
            tp != "MappingModeConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
        and (
            tp != "WrappingModeConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
        and (
            tp != "MagnificationFilterConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
        and (
            tp != "MinificationFilterConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
        and (
            tp != "InterpolationModeConstant"
        )  # https://threejs.org/docs/?q=KeyframeTrack#api/en/constants/Animation
        and (
            tp != "EncodingConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
    ):
        raise ValueError(tp)
######


# Obj and Array checking
directives = []

RAYCASTER_INTERSECTIONS = ArrayArg(
    val=ObjectArg(
        vals=[
            Arg("distance", "Number"),
            Arg("point", "Vector3"),
            Arg("face", "Face"),
            Arg("faceIndex", "Integer"),
            Arg("object", "Object3D"),
            Arg("uv", OptionalArg("Vector2")),
            Arg("uv2", OptionalArg("Vector2")),
            Arg("instanceId", OptionalArg("Integer")),
        ]
    )
)
# PLACEHOLDER = "Array"
for fi in FILES:
    if fi.name == "UniformsUtils":
        # merge uniforms
        fi.methods[1].args[0].tp = ArrayArg(val="UniformDefinition")
    elif fi.name == "WebGLRenderer":
        # clippingPlanes
        fi.properties[6].tp = ArrayArg(val="Plane")
    elif fi.name == "WebGLMultipleRenderTargets":
        # texture
        fi.properties[1].tp = ArrayArg(val="Texture")
    elif fi.name == "Texture":
        # mipmaps
        fi.properties[5].tp = ArrayArg(val="Image")  # is this correct?
    elif fi.name == "CompressedTexture":
        # mipmaps
        fi.ctor.args[0].tp = ArrayArg(val="Image")  # is this correct?
    elif fi.name == "Material":
        # clippingPlanes
        fi.properties[10].tp = ArrayArg(val="Plane")
    elif fi.name == "BufferAttribute":
        # copyArray array
        fi.methods[6].args[0].tp = UnionArg(
            left=ArrayArg(val="Number"), right="TypedArray"
        )
        # set value
        fi.methods[13].args[0].tp = UnionArg(
            left=ArrayArg(val="Number"), right="TypedArray"
        )
    elif fi.name == "Object3D":
        # children
        fi.properties[2].tp = ArrayArg(val="Object3D")
        # add objects
        fi.methods[0].args[0].tp = ArrayArg(val="Object3D")
        # raycast RETVAL
        fi.methods[15].retval = ArrayArg(val="Object3D")
        # raycast intersects
        fi.methods[15].args[1].tp = ArrayArg(val="Object3D")
        # remove objects
        fi.methods[16].args[0].tp = ArrayArg(val="Object3D")
    elif fi.name == "BufferGeometry":
        # groups
        fi.properties[4].tp = ArrayArg(
            val=ObjectArg(
                vals=[
                    Arg(name="start", tp="Integer"),
                    Arg(name="count", tp="Integer"),
                    Arg(name="materialIndex", tp="Integer"),
                ]
            )
        )
        # setFromPoints points
        fi.methods[24].args[0].tp = ArrayArg(val="Vector3")
    elif fi.name == "InterleavedBuffer":
        # array
        fi.properties[0].tp = "TypedArray"
    elif fi.name == "Raycaster":
        # intersectObject RETVAL
        fi.methods[2].retval = RAYCASTER_INTERSECTIONS
        # intersectObject optionalTarget
        ### We lob this off in our API
        ### hackish, but works
        fi.methods[2].args.pop(2)
        # intersectObjects RETVAL
        fi.methods[3].retval = RAYCASTER_INTERSECTIONS
        # intersectObjects objects
        fi.methods[3].args[0].tp = ArrayArg(val="Object3D")
        # intersectObjects optionalTarget
        ### We lob this off in our API
        ### hackish, but works
        fi.methods[3].args.pop(2)
    elif fi.name == "StringKeyframeTrack":
        # times
        fi.ctor.args[1].tp = ArrayArg(val="Number")
        # values
        fi.ctor.args[2].tp = ArrayArg(val="Number")
        # ValueBufferType
        fi.properties[1].tp = ArrayArg(val="Number")
    elif fi.name == "QuaternionKeyframeTrack":
        # times
        fi.ctor.args[1].tp = ArrayArg(val="Number")
        # values
        fi.ctor.args[2].tp = ArrayArg(val="Number")
    elif fi.name == "VectorKeyframeTrack":
        # times
        fi.ctor.args[1].tp = ArrayArg(val="Number")
        # values
        fi.ctor.args[2].tp = ArrayArg(val="Number")
    elif fi.name == "BooleanKeyframeTrack":
        # times
        fi.ctor.args[1].tp = ArrayArg(val="Number")
        # values
        fi.ctor.args[2].tp = ArrayArg(val="Number")
        # ValueBufferType
        fi.properties[1].tp = ArrayArg(val="Number")
    elif fi.name == "NumberKeyframeTrack":
        # times
        fi.ctor.args[1].tp = ArrayArg(val="Number")
        # values
        fi.ctor.args[2].tp = ArrayArg(val="Number")
    elif fi.name == "ColorKeyframeTrack":
        # times
        fi.ctor.args[1].tp = ArrayArg(val="Number")
        # values
        fi.ctor.args[2].tp = ArrayArg(val="Number")
    elif fi.name == "AnimationClip":
        # tracks
        fi.ctor.args[2].tp = ArrayArg(val="KeyframeTrack")
        # tracks
        fi.properties[3].tp = ArrayArg(val="KeyframeTrack")
    elif fi.name == "KeyframeTrack":
        # times
        fi.ctor.args[1].tp = ArrayArg(val="Number")
        # values
        fi.ctor.args[2].tp = ArrayArg(val="Number")
    elif fi.name == "AnimationObjectGroup":
        # objects
        fi.ctor.args[0].tp = ArrayArg(val="Mesh")
        # add objects
        fi.methods[0].args[0].tp = ArrayArg(val="Mesh")
        # remove objects
        fi.methods[1].args[0].tp = ArrayArg(val="Mesh")
        # uncache objects
        fi.methods[2].args[0].tp = ArrayArg(val="Mesh")
    elif fi.name == "Sprite":
        # raycast intersects
        fi.methods[2].args[1].tp = RAYCASTER_INTERSECTIONS
    elif fi.name == "Skeleton":
        # bones
        fi.ctor.args[0].tp = ArrayArg(val="Bone")
        # boneInverses
        fi.ctor.args[1].tp = ArrayArg(val="Matrix4")
        # bones
        fi.properties[0].tp = ArrayArg(val="Bone")
        # boneInverses
        fi.properties[1].tp = ArrayArg(val="Matrix4")
    elif fi.name == "LOD":
        # levels
        fi.properties[2].tp = ArrayArg(
            val=ObjectArg(vals=[Arg("object", "Object3D"), Arg("distance", "Number")])
        )
        # raycast RETVAL
        ### there's currently a bug in the source where this is
        ### _not_ correct, it should return an array but it doesn't
        fi.methods[4].retval = "undefined"
        # raycast intersects
        ### hack, pop it off
        fi.methods[4].args[1].tp = MutableArrayArg(val=RAYCASTER_INTERSECTIONS)
    elif fi.name == "Points":
        # morphTargetInfluences
        fi.properties[3].tp = ArrayArg(val="Number")
        # raycast intersects
        fi.methods[0].args[1].tp = MutableArrayArg(val=RAYCASTER_INTERSECTIONS)
    elif fi.name == "Mesh":
        # morphTargetInfluences
        fi.properties[3].tp = ArrayArg(val="Number")
        # raycast intersects
        fi.methods[1].args[1].tp = MutableArrayArg(val=RAYCASTER_INTERSECTIONS)
    elif fi.name == "Line":
        # morphTargetInfluences
        fi.properties[3].tp = ArrayArg(val="Number")
        # raycast intersects
        fi.methods[1].args[1].tp = MutableArrayArg(val=RAYCASTER_INTERSECTIONS)
    elif fi.name == "ArrayCamera":
        # array
        fi.ctor.args[0].tp = ArrayArg(val="Camera")
        # cameras
        fi.properties[0].tp = ArrayArg(val="Camera")
    elif fi.name == "LinearInterpolant":
        # evaluate RETVAL
        fi.methods[0].retval = "FloatArray32"
    elif fi.name == "CubicInterpolant":
        # evaluate RETVAL
        fi.methods[0].retval = "FloatArray32"
    elif fi.name == "DiscreteInterpolant":
        # evaluate RETVAL
        fi.methods[0].retval = "FloatArray32"
    elif fi.name == "QuaternionLinearInterpolant":
        # evaluate RETVAL
        fi.methods[0].retval = "FloatArray32"
    elif fi.name == "Triangle":
        # setFromPointsAndIndices points
        fi.methods[15].args[0].tp = ArrayArg(val="Vector3")
    elif fi.name == "SphericalHarmonics3":
        # coefficients
        fi.properties[0].tp = ArrayArg(val="Vector3")
        # fromArray array
        fi.methods[5].args[0].tp = ArrayArg(val="Number")
        # set coefficients
        fi.methods[10].args[0].tp = ArrayArg(val="Vector3")
        # toArray RETVAL
        fi.methods[11].retval = ArrayArg(val="Number")
        # toArray array
        ### hack, make it pure
        fi.methods[11].args = []
    elif fi.name == "Matrix3":
        # elements
        fi.properties[0].tp = ArrayArg(val="Number")
        # fromArray array
        fi.methods[5].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[18].retval = ArrayArg(val="Number")
        # toArray array
        ### hack make pure
        fi.methods[18].args = []
        # transposeIntoArray array
        fi.methods[21].args[0].tp = MutableArrayArg(val="Number")
    elif fi.name == "Box2":
        # setFromPoints points
        fi.methods[19].args[0].tp = ArrayArg(val="Number")
    elif fi.name == "Vector2":
        # fromArray array
        fi.methods[21].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[47].retval = ArrayArg(val="Number")
        # toArray array
        # hack make pure
        fi.methods[47].args = []
    elif fi.name == "Frustum":
        # planes
        fi.properties[0].tp = ArrayArg(val="Plane")
    elif fi.name == "Interpolant":
        # evaluate RETVAL
        fi.methods[0].retval = "FloatArray32"
    elif fi.name == "Vector3":
        # fromArray array
        fi.methods[27].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[67].retval = ArrayArg(val="Number")
        # toArray array
        ### hack make pure
        fi.methods[67].args = []
    elif fi.name == "Sphere":
        # setFromPoints points
        fi.methods[15].args[0].tp = ArrayArg(val="Vector3")
    elif fi.name == "Box3":
        # setFromArray array
        fi.methods[24].args[0].tp = ArrayArg(val="Number")
        # setFromPoints points
        fi.methods[28].args[0].tp = ArrayArg(val="Vector3")
    elif fi.name == "Vector4":
        # fromArray array
        fi.methods[15].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[44].retval = ArrayArg(val="Number")
        # toArray array
        ### hack make pure
        fi.methods[44].args = []
    elif fi.name == "Quaternion":
        # fromArray array
        fi.methods[6].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[24].retval = ArrayArg(val="Number")
        # toArray array
        ### hack make pure
        fi.methods[24].args = []
    elif fi.name == "Matrix4":
        # elements
        fi.properties[0].tp = ArrayArg(val="Number")
        # fromArray array
        fi.methods[9].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[35].retval = ArrayArg(val="Number")
        ### hack make pure
        fi.methods[35].args = []
    elif fi.name == "Color":
        # fromArray array
        fi.methods[10].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[30].retval = ArrayArg(val="Number")
        # toArray array
        ### hack make pure
        fi.methods[30].args = []
    elif fi.name == "Euler":
        # fromArray array
        fi.methods[3].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[9].retval = ArrayArg(val="Number")
        # toArray array
        ### hack make pure
        fi.methods[9].args = []
    elif fi.name == "TubeGeometry":
        # tangents
        fi.properties[1].tp = ArrayArg(val="Vector3")
        # normals
        fi.properties[2].tp = ArrayArg(val="Vector3")
        # binormals
        fi.properties[3].tp = ArrayArg(val="Vector3")
    elif fi.name == "ExtrudeGeometry":
        # shapes
        fi.ctor.args[0].tp = ArrayArg(val="Shape")
    elif fi.name == "LatheGeometry":
        # points
        fi.ctor.args[0].tp = ArrayArg(val="Vector3")
    elif fi.name == "ShapeGeometry":
        # shapes
        fi.ctor.args[0].tp = ArrayArg(val="Shape")
    elif fi.name == "PolyhedronGeometry":
        # vertices
        fi.ctor.args[0].tp = ArrayArg(val="OneOrMinusOne")
        # indices
        fi.ctor.args[1].tp = ArrayArg(val="Integer")
    elif fi.name == "AnimationLoader":
        # parse RETVAL
        fi.methods[1].retval = ArrayArg(val="AnimationClip")
    elif fi.name == "SkeletonHelper":
        # bones
        fi.properties[0].tp = ArrayArg(val="Bone")
    elif fi.name == "CurvePath":
        # curves
        fi.properties[0].tp = ArrayArg(val="Curve")
        # getCurveLengths RETVAL
        fi.methods[2].retval = ArrayArg(val="Number")
        # getPoints RETVAL
        fi.methods[3].retval = ArrayArg(val="Vector2")
        # getSpacedPoints RETVAL
        fi.methods[4].retval = ArrayArg(val="Vector2")
    elif fi.name == "ShapePath":
        # subPaths
        fi.properties[0].tp = ArrayArg(val="Path")
        # currentPath
        fi.properties[1].tp = ArrayArg(val="Path")
        # splineThru points
        fi.methods[4].args[0].tp = ArrayArg(val="Vector2")
        # toShapes RETVAL
        fi.methods[5].retval = ArrayArg(val="Shape")
    elif fi.name == "Curve":
        # getPoints RETVAL
        fi.methods[2].retval = ArrayArg(val="Vector2")
        # getSpacedPoints RETVAL
        fi.methods[3].retval = ArrayArg(val="Vector2")
        # getLengths RETVAL
        fi.methods[5].retval = ArrayArg(val="Number")
    elif fi.name == "Shape":
        # points
        fi.ctor.args[0].tp = ArrayArg(val="Vector2")
        # holes
        fi.properties[1].tp = ArrayArg(val="Vector2")
        # extractPoints RETVAL
        fi.methods[0].retval = ArrayArg(val="Vector2")
        # getPointsHoles RETVAL
        fi.methods[1].retval = ArrayArg(val="Vector2")
    elif fi.name == "Path":
        # points
        fi.ctor.args[0].tp = ArrayArg(val="Vector2")
        # setFromPoints vector2s
        fi.methods[8].args[0].tp = ArrayArg(val="Vector2")
        # splineThru points
        fi.methods[9].args[0].tp = ArrayArg(val="Vector2")
    elif fi.name == "SplineCurve":
        # points
        fi.ctor.args[0].tp = ArrayArg(val="Vector2")
        # points
        fi.properties[0].tp = ArrayArg(val="Vector2")
    elif fi.name == "CatmullRomCurve3":
        # points
        fi.ctor.args[0].tp = ArrayArg(val="Vector2")
        # points
        fi.properties[0].tp = ArrayArg(val="Vector2")


for fi in FILES:
    if fi.name == "WebGLProgram":
        # getUniforms RETVAL
        fi.methods[0].retval = "UniformDefinition"
        # getAttributes RETVAL
        fi.methods[1].retval = "AttributeDefinition"
    elif fi.name == "UniformsUtils":
        # clone RETVAL
        fi.methods[0].retval = "UniformDefinition"
        # merge RETVAL
        fi.methods[1].retval = "UniformDefinition"
    elif fi.name == "Texture":
        # toJSON RETVAL
        fi.methods[2].retval = "JSON"
    elif fi.name == "Source":
        # toJSON RETVAL
        fi.methods[0].retval = "JSON"
    elif fi.name == "Scene":
        # toJSON RETVAL
        fi.methods[0].retval = "JSON"
    elif fi.name == "FogExp2":
        # toJSON RETVAL
        fi.methods[1].retval = "JSON"
    elif fi.name == "Fog":
        # toJSON RETVAL
        fi.methods[1].retval = "JSON"
    elif fi.name == "Material":
        # toJSON RETVAL
        fi.methods[6].retval = "JSON"
    elif fi.name == "Object3D":
        # toJSON RETVAL
        fi.methods[28].retval = "JSON"
    elif fi.name == "BufferGeometry":
        # toJSON RETVAL
        fi.methods[26].retval = "JSON"
    elif fi.name == "InterleavedBuffer":
        # toJSON RETVAL
        fi.methods[5].retval = "JSON"
    elif fi.name == "AnimationClip":
        # toJSON RETVAL
        fi.methods[3].retval = "JSON"
    elif fi.name == "LOD":
        # toJSON RETVAL
        fi.methods[5].retval = "JSON"
    elif fi.name == "OrthographicCamera":
        # toJSON RETVAL
        fi.methods[3].retval = "JSON"
    elif fi.name == "PerspectiveCamera":
        # toJSON RETVAL
        fi.methods[8].retval = "JSON"
    elif fi.name == "Color":
        # getHSL RETVAL
        fi.methods[14].retval = ObjectArg(
            vals=[Arg("h", "Number"), Arg("s", "Number"), Arg("l", "Number")]
        )
    elif fi.name == "ObjectLoader":
        # parseGeometries RETVAL
        fi.methods[2].retval = RecordArg(val="Geometry")
        # parseMaterials RETVAL
        fi.methods[3].retval = RecordArg(val="Material")
        # parseAnimations RETVAL
        fi.methods[4].retval = RecordArg(val="Animation")
        # parseImages RETVAL
        fi.methods[5].retval = RecordArg(val="Image")
        # parseTextures RETVAL
        fi.methods[6].retval = RecordArg(val="Texture")
    elif fi.name == "LightShadow":
        # toJSON RETVAL
        fi.methods[7].retval = "JSON"
    elif fi.name == "Light":
        # toJSON RETVAL
        fi.methods[2].retval = "JSON"
    elif fi.name == "Curve":
        # computeFrenetFrames RETVAL
        fi.methods[10].retval = ObjectArg(
            vals=[
                Arg("tangents", ArrayArg(val="Vector3")),
                Arg("normals", ArrayArg(val="Vector3")),
                Arg("binormals", ArrayArg(val="Vector3")),
            ]
        )
        # toJSON RETVAL
        fi.methods[13].retval = "JSON"
    elif fi.name == "ImageUtils":
        # sRGBToLinear RETVAL
        fi.methods[1].retval = ObjectArg(
            vals=[
                Arg("data", ArrayArg(val="ImageData")),
                Arg("width", ArrayArg(val="Number")),
                Arg("height", ArrayArg(val="Number")),
            ]
        )
CHECKING2 = "Object"
for run in [True]:

    def rprint(*args):
        if run:
            directives.append(args)

    for fi in FILES:
        #### logic for array replacement
        ####
        if fi.ctor is not None:
            for i in range(len(fi.ctor.args)):
                arg = fi.ctor.args[i]
                if arg == CHECKING2:
                    rprint(fi.name, "CTOR", fi.ctor.args[i].name, arg, i)
        if fi.properties is not None:
            for i in range(len(fi.properties)):
                prop_ = fi.properties[i]
                prop = prop_
                if prop == CHECKING2:
                    rprint(fi.name, "PROP", prop_.name, prop, i)
        if fi.methods is not None:
            for i in range(len(fi.methods)):
                method = fi.methods[i]
                if method.retval == CHECKING2:
                    rprint(fi.name, "RETVAL", method.name, i)
                for j in range(len(method.args)):
                    arg = method.args[j]
                    arg = arg
                    if arg == CHECKING2:
                        rprint(
                            fi.name,
                            "METHOD",
                            method.name,
                            arg,
                            i,
                            method.args[j].name,
                            j,
                        )

FILENAME = None
# for directive in directives:
#     if directive[0] != FILENAME:
#         FILENAME = directive[0]
#         print(f'elif fi.name == "{FILENAME}":')
#     if directive[1] == "CTOR":
#         print(f'    # {directive[2]}')
#         print(f'    fi.ctor.args[{directive[4]}].tp = PLACEHOLDER')
#     elif directive[1] == "PROP":
#         print(f'    # {directive[2]}')
#         print(f'    fi.properties[{directive[4]}].tp = PLACEHOLDER')
#     elif directive[1] == "RETVAL":
#         print(f'    # {directive[2]} RETVAL')
#         print(f'    fi.methods[{directive[3]}].retval = PLACEHOLDER')
#     elif directive[1] == "METHOD":
#         print(f'    # {directive[2]} {directive[5]}')
#         print(f'    fi.methods[{directive[4]}].args[{directive[6]}].tp = PLACEHOLDER')

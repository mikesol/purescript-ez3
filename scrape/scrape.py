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

def argsToDict(args):
    out = dict()
    for x in args:
        out[x.name] = x.tp
    return out

def dictToArgs(d):
    out = []
    for (k,v) in d.items():
        out.append(Arg(k,v))
    return out

@dataclass
class ObjectArg:
    vals: Sequence["ArgTp"]
    optionals: Sequence["ArgTp"]
    def __add__(self, other):
        myOptionals = argsToDict(self.optionals)
        myVals = argsToDict(self.vals)
        theirOptionals = argsToDict(other.optionals)
        theirVals = argsToDict(other.vals)
        for key in myOptionals.keys():
            if key in theirVals.keys():
                myVals[key] = myOptionals[key]
                del myVals[key]
        newVals = theirVals.items() + myVals.items()
        newOptionals = theirOptionals.items() + theirOptionals.items()
        return ObjectArg(optionals=dictToArgs(newOptionals),vals=dictToArgs(newVals))

@dataclass
class MutableObjectArg:
    vals: Sequence["ArgTp"]
    optionals: Sequence["ArgTp"]


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

# ADT 1 for parsing


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
        else "FormatsConstant"
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
        else "TypesConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "type")
        else "MappingModesConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "mapping")
        else "WrappingModesConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "wrapS")
        else "WrappingModesConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "wrapT")
        else "MagnificationFiltersConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "magFilter")
        else "MinificationFiltersConstant"
        if (p == "Constant")
        and (
            f == "DepthTexture"
            or f == "CompressedTexture"
            or f == "VideoTexture"
            or f == "CanvasTexture"
        )
        and (n == "minFilter")
        else "FormatsConstant"
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
                    # we use a special parser
                    constants = []
                    curElt = soup.find_all("h2")[0]
                    curName = curElt.string
                    while True:
                        curElt = curElt.next_sibling
                        if curElt is None:
                            break
                        # print(threeFile.name, curName)
                        if curElt.name == "h2":
                            curName = curElt.string
                        if (curElt.name == "code") and (curName != "Code Example"):
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
                            if curName is not None and "Internal" not in curName:
                                constants.append(
                                    Constant(
                                        name=curName.replace(" ", "").replace("/", "_")
                                        + "Constant",
                                        constants=consts,
                                    )
                                )
                    threeFile.constants = constants
                    FILES.append(threeFile)
                    continue
                # We look up the file in the actual source to see if it extends something
                if threeFile.name in SOURCE:
                    with open(SOURCE[threeFile.name]) as src:
                        lines = src.read().split("\n")
                        done = False
                        extends = None
                        i = 0
                        if threeFile.name == "BufferAttribute":
                            pass
                        else:
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
                # used internally, don't care
                if "Cache" == threeFile.name:
                    continue
                # Skip PropertyBinding for now as there's too much undocumented stuff, come back to it later
                if "PropertyBinding" == threeFile.name:
                    continue
                # Skip PropertyMixer for now as there's too much undocumented stuff in PropertyBinding, come back to it later
                if "PropertyMixer" == threeFile.name:
                    continue
                # Skip GLBufferAttribute for now, come back to it later
                if "GLBufferAttribute" == threeFile.name:
                    continue
                # AnimationUtils has some undocumente types, so skip it for now
                if threeFile.name in ["AnimationUtils"]:
                    continue
                # ShapeUtils has some undocumente types, so skip it for now
                if threeFile.name in ["ShapeUtils"]:
                    continue
                # Earcut has some undocumente types, so skip it for now
                if threeFile.name in ["Earcut"]:
                    continue
                # Skip the audio stuff
                # it'd be nice to have it eventually, but I don't need it,
                # so it's one less headache for now
                if "Audio" in threeFile.name:
                    continue
                h2s = [h2 for h2 in soup.find_all("h2") if h2.string == "Constructor"]
                if len(h2s) == 1:
                    ctorH2 = h2s[0]
                    ctorH3 = ctorH2
                    while True:
                        ctorH3 = ctorH3.next_sibling
                        if ctorH3.name == "h3":
                            # CubeTexture and Texture have a documented constructor but
                            # it shouldn't be exposed and it's not typed
                            if threeFile.name in ["CubeTexture", "Texture"]:
                                break
                            # DataTexture has some undocumented types, so skip it for now
                            if threeFile.name in ["DataTexture"]:
                                break
                            # SpotLightShadow takes an empty constructor
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
                            # DataArrayTexture does not have types,
                            # so we add them here
                            if threeFile.name == "DataArrayTexture":
                                params = [["Number", param[0]] for param in params]
                            # PropertyBinding has number parameters if they do not have
                            # an explicit type
                            if threeFile.name == "PropertyBinding":
                                params = [
                                    ["Number", param[0]] if len(param) == 1 else param
                                    for param in params
                                ]
                            # AnimationObjectGroup has a variable number of objects in the ctor
                            # we represent that using an array
                            if threeFile.name == "AnimationObjectGroup":
                                params = [["Array", "objects"]]
                            # LinearInterpolant, DiscreteInterpolant, QuaternionLinearInterpolant, CubicInterpolant are not documented, so hardcode it
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
                            # PropertyBinding has number parameters if they do not have
                            # an explicit type
                            if (threeFile.name == "PropertyBinding") and (
                                methodName == "Composite"
                            ):
                                params = [
                                    ["Number", param[0]] if len(param) == 1 else param
                                    for param in params
                                ]
                            # BufferArray lacks a type in the documentation
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
# Code to help identify tricky types
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
            tp != "FormatsConstant"
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
            tp != "TypesConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
        and (
            tp != "MappingModesConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
        and (
            tp != "WrappingModesConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
        and (
            tp != "MagnificationFiltersConstant"
        )  # https://threejs.org/docs/?q=DepthTexture#api/en/constants/Textures
        and (
            tp != "MinificationFiltersConstant"
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


###
# Shader properties
MATERIAL_PROPERTIES = ObjectArg(
    vals=[],
    optionals=[
        Arg("alphaTest", "Float"),
        # .alphaTest : Float
        # Sets the alpha value to be used when running an alpha test. The material will not be rendered if the opacity is lower than this value. Default is 0.
        Arg("alphaTest", "Float"),
        # .alphaToCoverage : Float
        # Enables alpha to coverage. Can only be used with MSAA-enabled contexts (meaning when the renderer was created with antialias parameter set to true). Default is false.
        Arg("blendDst", "Integer"),
        # .blendDst : Integer
        # Blending destination. Default is OneMinusSrcAlphaFactor. See the destination factors constants for all possible values.
        # The material's blending must be set to CustomBlending for this to have any effect.
        Arg("blendDstAlpha", "Integer"),
        # .blendDstAlpha : Integer
        # The transparency of the .blendDst. Uses .blendDst value if null. Default is null.
        Arg("blendEquation", "Integer"),
        # .blendEquation : Integer
        # Blending equation to use when applying blending. Default is AddEquation. See the blending equation constants for all possible values.
        # The material's blending must be set to CustomBlending for this to have any effect.
        Arg("blendEquationAlpha", "Integer"),
        # .blendEquationAlpha : Integer
        # The transparency of the .blendEquation. Uses .blendEquation value if null. Default is null.
        Arg("blending", "BlendingConstant"),
        # .blending : Blending
        # Which blending to use when displaying objects with this material.
        # This must be set to CustomBlending to use custom blendSrc, blendDst or blendEquation.
        # See the blending mode constants for all possible values. Default is NormalBlending.
        Arg("blendSrc", "Integer"),
        # .blendSrc : Integer
        # Blending source. Default is SrcAlphaFactor. See the source factors constants for all possible values.
        # The material's blending must be set to CustomBlending for this to have any effect.
        Arg("blendSrcAlpha", "Integer"),
        # .blendSrcAlpha : Integer
        # The transparency of the .blendSrc. Uses .blendSrc value if null. Default is null.
        Arg("clipIntersection", "Boolean"),
        # .clipIntersection : Boolean
        # Changes the behavior of clipping planes so that only their intersection is clipped, rather than their union. Default is false.
        Arg("clippingPlanes", ArrayArg("Plane")),
        # .clippingPlanes : Array
        # User-defined clipping planes specified as THREE.Plane objects in world space. These planes apply to the objects this material is attached to. Points in space whose signed distance to the plane is negative are clipped (not rendered). This requires WebGLRenderer.localClippingEnabled to be true. See the WebGL / clipping /intersection example. Default is null.
        Arg("clipShadows", "Boolean"),
        # .clipShadows : Boolean
        # Defines whether to clip shadows according to the clipping planes specified on this material. Default is false.
        Arg("colorWrite", "Boolean"),
        # .colorWrite : Boolean
        # Whether to render the material's color. This can be used in conjunction with a mesh's renderOrder property to create invisible objects that occlude other objects. Default is true.
        Arg("defines", "Foreign"),
        # .defines : Object
        # Custom defines to be injected into the shader. These are passed in form of an object literal, with key/value pairs. { MY_CUSTOM_DEFINE: '' , PI2: Math.PI * 2 }. The pairs are defined in both vertex and fragment shaders. Default is undefined.
        Arg("depthFunc", "Integer"),
        # .depthFunc : Integer
        # Which depth function to use. Default is LessEqualDepth. See the depth mode constants for all possible values.
        Arg("depthTest", "Boolean"),
        # .depthTest : Boolean
        # Whether to have depth test enabled when rendering this material. Default is true.
        Arg("depthWrite", "Boolean"),
        # .depthWrite : Boolean
        # Whether rendering this material has any effect on the depth buffer. Default is true.
        # When drawing 2D overlays it can be useful to disable the depth writing in order to layer several things together without creating z-index artifacts.
        Arg("isMaterial", "Boolean"),
        # .isMaterial : Boolean
        # Read-only flag to check if a given object is of type Material.
        Arg("stencilWrite", "Boolean"),
        # .stencilWrite : Boolean
        # Whether stencil operations are performed against the stencil buffer. In order to perform writes or comparisons against the stencil buffer this value must be true. Default is false.
        Arg("stencilWriteMask", "Integer"),
        # .stencilWriteMask : Integer
        # The bit mask to use when writing to the stencil buffer. Default is 0xFF.
        Arg("stencilFunc", "Integer"),
        # .stencilFunc : Integer
        # The stencil comparison function to use. Default is AlwaysStencilFunc. See stencil function constants for all possible values.
        Arg("stencilRef", "Integer"),
        # .stencilRef : Integer
        # The value to use when performing stencil comparisons or stencil operations. Default is 0.
        Arg("stencilFuncMask", "Integer"),
        # .stencilFuncMask : Integer
        # The bit mask to use when comparing against the stencil buffer. Default is 0xFF.
        Arg("stencilFail", "Integer"),
        # .stencilFail : Integer
        # Which stencil operation to perform when the comparison function returns false. Default is KeepStencilOp. See the stencil operations constants for all possible values.
        Arg("stencilZFail", "Integer"),
        # .stencilZFail : Integer
        # Which stencil operation to perform when the comparison function returns true but the depth test fails. Default is KeepStencilOp. See the stencil operations constants for all possible values.
        Arg("stencilZPass", "Integer"),
        # .stencilZPass : Integer
        # Which stencil operation to perform when the comparison function returns true and the depth test passes. Default is KeepStencilOp. See the stencil operations constants for all possible values.
        Arg("id", "Integer"),
        # .id : Integer
        # Unique number for this material instance.
        Arg("name", "String"),
        # .name : String
        # Optional name of the object (doesn't need to be unique). Default is an empty string.
        Arg("needsUpdate", "Boolean"),
        # .needsUpdate : Boolean
        # Specifies that the material needs to be recompiled.
        Arg("opacity", "Float"),
        # .opacity : Float
        # Float in the range of 0.0 - 1.0 indicating how transparent the material is. A value of 0.0 indicates fully transparent, 1.0 is fully opaque.
        # If the material's transparent property is not set to true, the material will remain fully opaque and this value will only affect its color.
        # Default is 1.0.
        Arg("polygonOffset", "Boolean"),
        # .polygonOffset : Boolean
        # Whether to use polygon offset. Default is false. This corresponds to the GL_POLYGON_OFFSET_FILL WebGL feature.
        Arg("polygonOffsetFactor", "Integer"),
        # .polygonOffsetFactor : Integer
        # Sets the polygon offset factor. Default is 0.
        Arg("polygonOffsetUnits", "Integer"),
        # .polygonOffsetUnits : Integer
        # Sets the polygon offset units. Default is 0.
        Arg("precision", "String"),
        # .precision : String
        # Override the renderer's default precision for this material. Can be "highp", "mediump" or "lowp". Default is null.
        Arg("premultipliedAlpha", "Boolean"),
        # .premultipliedAlpha : Boolean
        # Whether to premultiply the alpha (transparency) value. See WebGL / Materials / Physical / Transmission for an example of the difference. Default is false.
        Arg("dithering", "Boolean"),
        # .dithering : Boolean
        # Whether to apply dithering to the color to remove the appearance of banding. Default is false.
        Arg("shadowSide", "Integer"),
        # .shadowSide : Integer
        # Defines which side of faces cast shadows. When set, can be THREE.FrontSide, THREE.BackSide, or THREE.DoubleSide. Default is null.
        # If null, the side casting shadows is determined as follows:
        # Material.side	Side casting shadows
        # THREE.FrontSide	back side
        # THREE.BackSide	front side
        # THREE.DoubleSide	both sides
        # .side : Integer
        # Defines which side of faces will be rendered - front, back or both. Default is THREE.FrontSide. Other options are THREE.BackSide and THREE.DoubleSide.
        Arg("toneMapped", "Boolean"),
        # .toneMapped : Boolean
        # Defines whether this material is tone mapped according to the renderer's toneMapping setting. Default is true.
        Arg("transparent", "Boolean"),
        # .transparent : Boolean
        # Defines whether this material is transparent. This has an effect on rendering as transparent objects need special treatment and are rendered after non-transparent objects.
        # When set to true, the extent to which the material is transparent is controlled by setting its opacity property.
        # Default is false.
        Arg("type", "String"),
        # .type : String
        # Value is the string 'Material'. This shouldn't be changed, and can be used to find all objects of this type in a scene.
        Arg("uuid", "String"),
        # .uuid : String
        # UUID of this material instance. This gets automatically assigned, so this shouldn't be edited.
        Arg("version", "Integer"),
        # .version : Integer
        # This starts at 0 and counts how many times .needsUpdate is set to true.
        Arg("vertexColors", "Boolean"),
        # .vertexColors : Boolean
        # Defines whether vertex coloring is used. Default is false.
        Arg("visible", "Boolean"),
        # .visible : Boolean
        # Defines whether this material is visible. Default is true.
        Arg("userData", "Foreign"),
        # .userData : Object
        # An object that can be used to store custom data about the Material. It should not hold references to functions as these will not be cloned.
    ],
)


MESH_BASIC_MATERIAL_PROPERTIES = ObjectArg(
    vals=[],
    optionals=[
        Arg("alphaMap", "Texture"),
        # .alphaMap : Texture
        # The alpha map is a grayscale texture that controls the opacity across the surface (black: fully transparent; white: fully opaque). Default is null.
        # Only the color of the texture is used, ignoring the alpha channel if one exists. For RGB and RGBA textures, the WebGL renderer will use the green channel when sampling this texture due to the extra bit of precision provided for green in DXT-compressed and uncompressed RGB 565 formats. Luminance-only and luminance/alpha textures will also still work as expected.
        Arg("aoMap", "Texture"),
        # .aoMap : Texture
        # The red channel of this texture is used as the ambient occlusion map. Default is null. The aoMap requires a second set of UVs.
        Arg("aoMapIntensity", "Float"),
        # .aoMapIntensity : Float
        # Intensity of the ambient occlusion effect. Default is 1. Zero is no occlusion effect.
        Arg("color", "Color"),
        # .color : Color
        # Color of the material, by default set to white (0xffffff).
        Arg("combine", "Integer"),
        # .combine : Integer
        # How to combine the result of the surface's color with the environment map, if any.
        # Options are THREE.MultiplyOperation (default), THREE.MixOperation, THREE.AddOperation. If mix is chosen, the .reflectivity is used to blend between the two colors.
        Arg("envMap", "Texture"),
        # .envMap : Texture
        # The environment map. Default is null.
        Arg("fog", "Boolean"),
        # .fog : Boolean
        # Whether the material is affected by fog. Default is true.
        Arg("lightMap", "Texture"),
        # .lightMap : Texture
        # The light map. Default is null. The lightMap requires a second set of UVs.
        Arg("lightMapIntensity", "Float"),
        # .lightMapIntensity : Float
        # Intensity of the baked light. Default is 1.
        Arg("map", "Texture"),
        # .map : Texture
        # The color map. May optionally include an alpha channel, typically combined with .transparent or .alphaTest. Default is null.
        Arg("reflectivity", "Float"),
        # .reflectivity : Float
        # How much the environment map affects the surface; also see .combine. The default value is 1 and the valid range is between 0 (no reflections) and 1 (full reflections).
        Arg("refractionRatio", "Float"),
        # .refractionRatio : Float
        # The index of refraction (IOR) of air (approximately 1) divided by the index of refraction of the material. It is used with environment mapping modes THREE.CubeRefractionMapping and THREE.EquirectangularRefractionMapping. The refraction ratio should not exceed 1. Default is 0.98.
        Arg("specularMap", "Texture"),
        # .specularMap : Texture
        # Specular map used by the material. Default is null.
        Arg("wireframe", "Boolean"),
        # .wireframe : Boolean
        # Render geometry as wireframe. Default is false (i.e. render as flat polygons).
        Arg("wireframeLinecap", "String"),
        # .wireframeLinecap : String
        # Define appearance of line ends. Possible values are "butt", "round" and "square". Default is 'round'.
        # This corresponds to the 2D Canvas lineCap property and it is ignored by the WebGL renderer.
        Arg("wireframeLinejoin", "String"),
        # .wireframeLinejoin : String
        # Define appearance of line joints. Possible values are "round", "bevel" and "miter". Default is 'round'.
        # This corresponds to the 2D Canvas lineJoin property and it is ignored by the WebGL renderer.
        Arg("wireframeLinewidth", "Float"),
        # .wireframeLinewidth : Float
        # Controls wireframe thickness. Default is 1.
    ],
)
directives = []

WEBGL_CTOR_PARAMS = ObjectArg(
    optionals=[
        Arg("canvas", "HTMLCanvasElement"),
        Arg("context", "WebGLContext"),
        Arg("precision", "ShaderPrecision"),
        Arg("alpha", "Boolean"),
        Arg("premultipliedAlpha", "Boolean"),
        Arg("antialias", "Boolean"),
        Arg("stencil", "Boolean"),
        Arg("preserveDrawingBuffer", "Boolean"),
        Arg("powerPreference", "PowerPreference"),
        Arg("failIfMajorPerformanceCaveat", "Boolean"),
        Arg("depth", "Boolean"),
        Arg("logarithmicDepthBuffer", "Boolean"),
    ],
    vals=[],
)

RENDERER_OPTIONS = ObjectArg(
    optionals=[],
    vals=[
        Arg("wrapS", "WrappingModesConstant"),
        Arg("wrapT", "WrappingModesConstant"),
        Arg("magFilter", "MagnificationFiltersConstant"),
        Arg("minFilter", "MinificationFiltersConstant"),
        Arg("generateMipmaps", "Boolean"),
        Arg("format", "FormatsConstant"),
        Arg("type", "TypesConstant"),
        Arg("anisotropy", "Number"),
        Arg("encoding", "EncodingConstant"),
        Arg("depthBuffer", "Boolean"),
        Arg("stencilBuffer", "Boolean"),
        Arg("samples", "Number"),
    ],
)

CAMERA_VIEW_PARAMS = ObjectArg(
    optionals=[],
    vals=[
        Arg("fullWidth", "Number"),
        Arg("fullHeight", "Number"),
        Arg("x", "Number"),
        Arg("y", "Number"),
        Arg("width", "Number"),
        Arg("height", "Number"),
    ],
)

UNIFORM_CAN_BE = UnionArg(
    "Number",
    UnionArg(
        "Boolean",
        UnionArg(
            "Vector2",
            UnionArg(
                "Vector3",
                UnionArg(
                    ArrayArg("Number"),
                    UnionArg(
                        "Float32Array",
                        UnionArg(
                            "Color",
                            UnionArg(
                                "Quaternion",
                                UnionArg(
                                    "Int32Array",
                                    UnionArg(
                                        "Vector4",
                                        UnionArg(
                                            "CubeTexture",
                                            UnionArg(
                                                "Matrix3",
                                                UnionArg("Matrix4", "Texture"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
)

EXTRUDE_GEOMETRY_OPTIONS = ObjectArg(
    optionals=[
        Arg("curveSegments", "Integer"),
        Arg("steps", "Integer"),
        Arg("depth", "Number"),
        Arg("bevelEnabled", "Boolean"),
        Arg("bevelThickness", "Number"),
        Arg("bevelSize", "Number"),
        Arg("bevelOffset", "Number"),
        Arg("bevelSegments", "Integer"),
        Arg("extrudePath", "Curve"),
        # for now, leave out UVGenerator as I have no clue
        # how to represent this
        # Arg("UVGenerator", "???"),
    ],
    vals=[],
)

RAYCASTER_INTERSECTIONS = ArrayArg(
    val=ObjectArg(
        optionals=[],
        vals=[
            Arg("distance", "Number"),
            Arg("point", "Vector3"),
            Arg("face", "Face"),
            Arg("faceIndex", "Integer"),
            Arg("object", "Object3D"),
            Arg("uv", OptionalArg("Vector2")),
            Arg("uv2", OptionalArg("Vector2")),
            Arg("instanceId", OptionalArg("Integer")),
        ],
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
                optionals=[],
                vals=[
                    Arg(name="start", tp="Integer"),
                    Arg(name="count", tp="Integer"),
                    Arg(name="materialIndex", tp="Integer"),
                ],
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
        # We lob this off in our API
        # hackish, but works
        fi.methods[2].args.pop(2)
        # intersectObjects RETVAL
        fi.methods[3].retval = RAYCASTER_INTERSECTIONS
        # intersectObjects objects
        fi.methods[3].args[0].tp = ArrayArg(val="Object3D")
        # intersectObjects optionalTarget
        # We lob this off in our API
        # hackish, but works
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
            val=ObjectArg(
                optionals=[],
                vals=[Arg("object", "Object3D"), Arg("distance", "Number")],
            )
        )
        # raycast RETVAL
        # there's currently a bug in the source where this is
        # _not_ correct, it should return an array but it doesn't
        fi.methods[4].retval = "undefined"
        # raycast intersects
        # hack, pop it off
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
        # hack, make it pure
        fi.methods[11].args = []
    elif fi.name == "Matrix3":
        # elements
        fi.properties[0].tp = ArrayArg(val="Number")
        # fromArray array
        fi.methods[5].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[18].retval = ArrayArg(val="Number")
        # toArray array
        # hack make pure
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
        # hack make pure
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
        # hack make pure
        fi.methods[44].args = []
    elif fi.name == "Quaternion":
        # fromArray array
        fi.methods[6].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[24].retval = ArrayArg(val="Number")
        # toArray array
        # hack make pure
        fi.methods[24].args = []
    elif fi.name == "Matrix4":
        # elements
        fi.properties[0].tp = ArrayArg(val="Number")
        # fromArray array
        fi.methods[9].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[35].retval = ArrayArg(val="Number")
        # hack make pure
        fi.methods[35].args = []
    elif fi.name == "Color":
        # fromArray array
        fi.methods[10].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[30].retval = ArrayArg(val="Number")
        # toArray array
        # hack make pure
        fi.methods[30].args = []
    elif fi.name == "Euler":
        # fromArray array
        fi.methods[3].args[0].tp = ArrayArg(val="Number")
        # toArray RETVAL
        fi.methods[9].retval = ArrayArg(val="Number")
        # toArray array
        # hack make pure
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
        fi.ctor.args[0].tp = ArrayArg(val="Vector2")
    elif fi.name == "ShapeGeometry":
        # shapes
        fi.ctor.args[0].tp = UnionArg["Shape", ArrayArg("Shape")]
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
        fi.methods[14].retval = MutableObjectArg(
            optionals=[],
            vals=[Arg("h", "Number"), Arg("s", "Number"), Arg("l", "Number")],
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
            optionals=[],
            vals=[
                Arg("tangents", ArrayArg(val="Vector3")),
                Arg("normals", ArrayArg(val="Vector3")),
                Arg("binormals", ArrayArg(val="Vector3")),
            ],
        )
        # toJSON RETVAL
        fi.methods[13].retval = "JSON"
    elif fi.name == "ImageUtils":
        # sRGBToLinear RETVAL
        fi.methods[1].retval = ObjectArg(
            optionals=[],
            vals=[
                Arg("data", ArrayArg(val="ImageData")),
                Arg("width", ArrayArg(val="Number")),
                Arg("height", ArrayArg(val="Number")),
            ],
        )
    elif fi.name == "WebGLRenderer":
        # parameters
        # canvas - A canvas where the renderer draws its output. This corresponds to the domElement property below. If not passed in here, a new canvas element will be created.
        # context - This can be used to attach the renderer to an existing RenderingContext. Default is null.
        # precision - Shader precision. Can be "highp", "mediump" or "lowp". Defaults to "highp" if supported by the device.
        # alpha - controls the default clear alpha value. When set to true, the value is 0. Otherwise it's 1. Default is false.
        # premultipliedAlpha - whether the renderer will assume that colors have premultiplied alpha. Default is true.
        # antialias - whether to perform antialiasing. Default is false.
        # stencil - whether the drawing buffer has a stencil buffer of at least 8 bits. Default is true.
        # preserveDrawingBuffer - whether to preserve the buffers until manually cleared or overwritten. Default is false.
        # powerPreference - Provides a hint to the user agent indicating what configuration of GPU is suitable for this WebGL context. Can be "high-performance", "low-power" or "default". Default is "default". See WebGL spec for details.
        # failIfMajorPerformanceCaveat - whether the renderer creation will fail upon low performance is detected. Default is false. See WebGL spec for details.
        # depth - whether the drawing buffer has a depth buffer of at least 16 bits. Default is true.
        # logarithmicDepthBuffer - whether to use a logarithmic depth buffer. It may be necessary to use this if dealing with huge differences in scale in a single scene. Note that this setting uses gl_FragDepth if available which disables the Early Fragment Test optimization and can cause a decrease in performance. Default is false. See the camera / logarithmicdepthbuffer example.
        fi.ctor.args[0].tp = WEBGL_CTOR_PARAMS
        # debug
        fi.properties[4].tp = ObjectArg(
            optionals=[], vals=[Arg("checkShaderErrors", "Boolean")]
        )
        # capabilities
        # - floatFragmentTextures: whether the context supports the OES_texture_float extension.
        # - floatVertexTextures: true if floatFragmentTextures and vertexTextures are both true.
        # - getMaxAnisotropy(): Returns the maximum available anisotropy.
        # - getMaxPrecision(): Returns the maximum available precision for vertex and fragment shaders.
        # - isWebGL2: true if the context in use is a WebGL2RenderingContext object.
        # - logarithmicDepthBuffer: true if the logarithmicDepthBuffer was set to true in the constructor and the context supports the EXT_frag_depth extension.
        # - maxAttributes: The value of gl.MAX_VERTEX_ATTRIBS.
        # - maxCubemapSize: The value of gl.MAX_CUBE_MAP_TEXTURE_SIZE. Maximum height * width of cube map textures that a shader can use.
        # - maxFragmentUniforms: The value of gl.MAX_FRAGMENT_UNIFORM_VECTORS. The number of uniforms that can be used by a fragment shader.
        # - maxSamples: The value of gl.MAX_SAMPLES. Maximum number of samples in context of Multisample anti-aliasing (MSAA).
        # - maxTextureSize: The value of gl.MAX_TEXTURE_SIZE. Maximum height * width of a texture that a shader use.
        # - maxTextures: The value of gl.MAX_TEXTURE_IMAGE_UNITS. The maximum number of textures that can be used by a shader.
        # - maxVaryings: The value of gl.MAX_VARYING_VECTORS. The number of varying vectors that can used by shaders.
        # - maxVertexTextures: The value of gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS. The number of textures that can be used in a vertex shader.
        # - maxVertexUniforms: The value of gl.MAX_VERTEX_UNIFORM_VECTORS. The maximum number of uniforms that can be used in a vertex shader.
        # - precision: The shader precision currently being used by the renderer.
        # - vertexTextures: true if .maxVertexTextures : Integeris greater than 0 (i.e. vertex textures can be used).
        fi.properties[5].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("floatFragmentTextures", "Boolean"),
                Arg("floatVertexTextures", "Boolean"),
                Arg("getMaxAnisotropy", "Effect Number"),
                Arg("getMaxPrecision", "Effect Number"),
                Arg("isWebGL2", "Boolean"),
                Arg("logarithmicDepthBuffer", "Boolean"),
                Arg("maxAttributes", "Integer"),
                Arg("maxCubemapSize", "Number"),
                Arg("maxFragmentUniforms", "Integer"),
                Arg("maxSamples", "Integer"),
                Arg("maxTextureSize", "Integer"),
                Arg("maxTextures", "Integer"),
                Arg("maxVaryings", "Integer"),
                Arg("maxVertexTextures", "Integer"),
                Arg("maxVertexUniforms", "Integer"),
                Arg("precision", "Number"),
                Arg("vertexTextures", "Boolean"),
            ],
        )
        # extensions
        fi.properties[8].tp = "Foreign"
        # info
        fi.properties[10].tp = "Foreign"
        # properties
        fi.properties[13].tp = "Foreign"
        # shadowMap
        # - enabled: If set, use shadow maps in the scene. Default is false.
        # - autoUpdate: Enables automatic updates to the shadows in the scene. Default is true.
        # If you do not require dynamic lighting / shadows, you may set this to false when the renderer is instantiated.
        # - needsUpdate: When set to true, shadow maps in the scene will be updated in the next render call. Default is false.
        # If you have disabled automatic updates to shadow maps (shadowMap.autoUpdate = false), you will need to set this to true and then make a render call to update the shadows in your scene.
        # - type: Defines shadow map type (unfiltered, percentage close filtering, percentage close filtering with bilinear filtering in shader). Options are:

        # THREE.BasicShadowMap
        # THREE.PCFShadowMap (default)
        # THREE.PCFSoftShadowMap
        # THREE.VSMShadowMap
        fi.properties[14].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("enabled", "Boolean"),
                Arg("autoUpdate", "Boolean"),
                Arg("needsUpdate", "Boolean"),
                Arg("type", "ShadowTypesConstant"),
            ],
        )
        # state
        fi.properties[16].tp = "Foreign"
    elif fi.name == "WebGL1Renderer":
        # parameters
        fi.ctor.args[0].tp = WEBGL_CTOR_PARAMS
    elif fi.name == "WebGLRenderTarget":
        # options
        fi.ctor.args[2].tp = RENDERER_OPTIONS
    elif fi.name == "WebGLCubeRenderTarget":
        # options
        fi.ctor.args[1].tp = RENDERER_OPTIONS
    elif fi.name == "WebGLMultipleRenderTargets":
        # options
        fi.ctor.args[3].tp = RENDERER_OPTIONS
    elif fi.name == "Texture":
        # userData
        fi.properties[29].tp = "Foreign"
        # toJSON meta
        fi.methods[2].args[0].tp = "Foreign"
    elif fi.name == "Source":
        # toJSON meta
        fi.methods[0].args[0].tp = "Foreign"
    elif fi.name == "Scene":
        # background
        fi.properties[0].tp = UnionArg("Color", UnionArg("Texture", "CubeTexture"))
        # toJSON meta
        fi.methods[0].args[0].tp = "Foreign"
    elif fi.name == "MeshLambertMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "MeshBasicMaterial":
        # parameters
        fi.ctor.args[0].tp = MESH_BASIC_MATERIAL_PROPERTIES + MATERIAL_PROPERTIES
    elif fi.name == "RawShaderMaterial":
        # parameters
        fi.ctor.args[0].tp = MATERIAL_PROPERTIES
    elif fi.name == "MeshPhysicalMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
        # defines
        fi.properties[8].tp = PLACEHOLDER
    elif fi.name == "Material":
        # defines
        fi.properties[13].tp = "Foreign"
        # userData
        fi.properties[45].tp = "Foreign"
        # setValues values
        fi.methods[5].args[0].tp = "Foreign"
        # toJSON meta
        fi.methods[6].args[0].tp = "Foreign"
    elif fi.name == "PointsMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "MeshStandardMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
        # defines
        fi.properties[6].tp = PLACEHOLDER
    elif fi.name == "ShadowMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "MeshMatcapMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "LineBasicMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "MeshToonMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "SpriteMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "MeshDepthMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "LineDashedMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "MeshDistanceMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "MeshNormalMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "ShaderMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
        # defaultAttributeValues
        fi.properties[1].tp = PLACEHOLDER
        # defines
        fi.properties[2].tp = PLACEHOLDER
        # extensions
        fi.properties[3].tp = PLACEHOLDER
        # uniforms
        fi.properties[12].tp = PLACEHOLDER
    elif fi.name == "MeshPhongMaterial":
        # parameters
        fi.ctor.args[0].tp = PLACEHOLDER
    elif fi.name == "BufferAttribute":
        # updateRange
        fi.properties[8].tp = ObjectArg(
            vals=[Arg("offset", "Integer"), Arg("count", "Integer")], optionals=[]
        )
    elif fi.name == "Object3D":
        # userData
        fi.properties[27].tp = "Foreign"
        # toJSON meta
        fi.methods[28].args[0].tp = "Foreign"
    elif fi.name == "EventDispatcher":
        # dispatchEvent event
        fi.methods[3].args[0].tp = ObjectArg(
            optionals=[], vals=[Arg("type", "String"), Arg("message", "String")]
        )
    elif fi.name == "BufferGeometry":
        # attributes
        fi.properties[0].tp = RecordArg("BufferAttribute")
        # drawRange
        fi.properties[3].tp = ObjectArg(
            optionals=[], vals=[Arg("start", "Integer"), Arg("count", "Integer")]
        )
        # morphAttributes
        fi.properties[8].tp = RecordArg("BufferAttribute")
        # userData
        fi.properties[11].tp = "Foreign"
    elif fi.name == "Uniform":
        # value
        fi.ctor.args[0].tp = UNIFORM_CAN_BE
        # value
        fi.properties[0].tp = UNIFORM_CAN_BE
    elif fi.name == "InterleavedBuffer":
        # updateRange
        fi.properties[3].tp = ObjectArg(
            vals=[Arg("offset", "Integer"), Arg("count", "Integer")], optionals=[]
        )
        # clone data
        fi.methods[3].args[0].tp = "Foreign"
        # toJSON data
        fi.methods[5].args[0].tp = "Foreign"
    elif fi.name == "Raycaster":
        # params
        fi.properties[4].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("Mesh", ObjectArg(optionals=[], vals=[])),
                Arg("Line", ObjectArg(optionals=[], vals=[Arg("threshold", "Number")])),
                Arg("LOD", ObjectArg(optionals=[], vals=[])),
                Arg(
                    "Points", ObjectArg(optionals=[], vals=[Arg("threshold", "Number")])
                ),
                Arg("Sprite", ObjectArg(optionals=[], vals=[])),
            ],
        )
    elif fi.name == "AnimationObjectGroup":
        # stats
        ### not documented, so make it foreign and hope for the best!
        fi.properties[1].tp = "Foreign"
    elif fi.name == "LOD":
        # toJSON meta
        fi.methods[5].args[0].tp = "Foreign"
    elif fi.name == "Points":
        # morphTargetDictionary
        ### I give up, no idea what to do here
        fi.properties[4].tp = "Foreign"
    elif fi.name == "Mesh":
        # morphTargetDictionary
        ### I give up, no idea what to do here
        fi.properties[4].tp = "Foreign"
    elif fi.name == "Line":
        # morphTargetDictionary
        ### I give up, no idea what to do here
        fi.properties[4].tp = "Foreign"
    elif fi.name == "OrthographicCamera":
        # view
        fi.properties[7].tp = CAMERA_VIEW_PARAMS
        # toJSON meta
        fi.methods[3].args[0].tp = "Foreign"
    elif fi.name == "PerspectiveCamera":
        # view
        # fullWidth — full width of multiview setup
        # fullHeight — full height of multiview setup
        # x — horizontal offset of subcamera
        # y — vertical offset of subcamera
        # width — width of subcamera
        # height — height of subcamera
        fi.properties[8].tp = CAMERA_VIEW_PARAMS
        # toJSON meta
        fi.methods[8].args[0].tp = "Foreign"
    elif fi.name == "LinearInterpolant":
        # settings
        fi.properties[3].tp = "Foreign"
    elif fi.name == "CubicInterpolant":
        # settings
        fi.properties[3].tp = "Foreign"
    elif fi.name == "DiscreteInterpolant":
        # settings
        fi.properties[3].tp = "Foreign"
    elif fi.name == "QuaternionLinearInterpolant":
        # settings
        fi.properties[3].tp = "Foreign"
    elif fi.name == "Interpolant":
        # settings
        ### as this is subclassed, leave it foreign
        fi.properties[3].tp = "Foreign"
    elif fi.name == "Color":
        # getHSL target
        fi.methods[14].args[0].tp = MutableObjectArg(
            optionals=[],
            vals=[Arg("h", "Number"), Arg("s", "Number"), Arg("l", "Number")],
        )
    elif fi.name == "TetrahedronGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[], vals=[Arg("radius", "Number"), Arg("detail", "Integer")]
        )
    elif fi.name == "BoxGeometry":
        # parameters
        # width — Width; that is, the length of the edges parallel to the X axis. Optional; defaults to 1.
        # height — Height; that is, the length of the edges parallel to the Y axis. Optional; defaults to 1.
        # depth — Depth; that is, the length of the edges parallel to the Z axis. Optional; defaults to 1.
        # widthSegments — Number of segmented rectangular faces along the width of the sides. Optional; defaults to 1.
        # heightSegments — Number of segmented rectangular faces along the height of the sides. Optional; defaults to 1.
        # depthSegments — Number of segmented rectangular faces along the depth of the sides. Optional; defaults to 1.
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("width", "Number"),
                Arg("height", "Number"),
                Arg("depth", "Number"),
                Arg("widthSegments", "Integer"),
                Arg("heightSegments", "Integer"),
                Arg("depthSegments", "Integer"),
            ],
        )
    elif fi.name == "TubeGeometry":
        # path — Curve - A 3D path that inherits from the Curve base class. Default is a quadratic bezier curve.
        # tubularSegments — Integer - The number of segments that make up the tube. Default is 64.
        # radius — Float - The radius of the tube. Default is 1.
        # radialSegments — Integer - The number of segments that make up the cross-section. Default is 8.
        # closed — Boolean Is the tube open or closed. Default is false.
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("path", "Curve"),
                Arg("tubularSegments", "Integer"),
                Arg("radius", "Number"),
                Arg("radialSegments", "Integer"),
                Arg("closed", "Boolean"),
            ],
        )
    elif fi.name == "ExtrudeGeometry":
        # options
        # curveSegments — int. Number of points on the curves. Default is 12.
        # steps — int. Number of points used for subdividing segments along the depth of the extruded spline. Default is 1.
        # depth — float. Depth to extrude the shape. Default is 1.
        # bevelEnabled — bool. Apply beveling to the shape. Default is true.
        # bevelThickness — float. How deep into the original shape the bevel goes. Default is 0.2.
        # bevelSize — float. Distance from the shape outline that the bevel extends. Default is bevelThickness - 0.1.
        # bevelOffset — float. Distance from the shape outline that the bevel starts. Default is 0.
        # bevelSegments — int. Number of bevel layers. Default is 3.
        # extrudePath — THREE.Curve. A 3D spline path along which the shape should be extruded. Bevels not supported for path extrusion.
        # UVGenerator — Object. object that provides UV generator functions
        fi.ctor.args[1].tp = EXTRUDE_GEOMETRY_OPTIONS
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("shapes", UnionArg(left="Shape", right=ArrayArg(val="Shape"))),
                Arg("options", EXTRUDE_GEOMETRY_OPTIONS),
            ],
        )
    elif fi.name == "CylinderGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("radiusTop", "Float"),
                Arg("radiusBottom", "Float"),
                Arg("height", "Float"),
                Arg("radialSegments", "Integer"),
                Arg("heightSegments", "Integer"),
                Arg("openEnded", "Boolean"),
                Arg("thetaStart", "Float"),
                Arg("thetaLength", "Float"),
            ],
        )
    elif fi.name == "EdgesGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("geometry", "BufferGeometry"),
                Arg("thresholdAngle", "Integer"),
            ],
        )
    elif fi.name == "LatheGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("points", ArrayArg(val="Vector2")),
                Arg("segments", "Integer"),
                Arg("phiStart", "Number"),
                Arg("phiStart", "Number"),
            ],
        )
    elif fi.name == "PlaneGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("width", "Number"),
                Arg("height", "Number"),
                Arg("widthSegments", "Integer"),
                Arg("heightSegments", "Integer"),
            ],
        )
    elif fi.name == "CircleGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("radius", "Number"),
                Arg("segments", "Integer"),
                Arg("thetaStart", "Number"),
                Arg("thetaLength", "Number"),
            ],
        )
    elif fi.name == "TorusKnotGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("radius", "Number"),
                Arg("tube", "Number"),
                Arg("radialSegments", "Integer"),
                Arg("tubularSegments", "Integer"),
                Arg("p", "Number"),
                Arg("q", "Number"),
            ],
        )
    elif fi.name == "ShapeGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("shapes", UnionArg["Shape", ArrayArg("Shape")]),
                Arg("curveSegments", "Integer"),
            ],
        )
    elif fi.name == "DodecahedronGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[], vals=[Arg("radius", "Number"), Arg("detail", "Integer")]
        )
    elif fi.name == "ConeGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("radius", "Number"),
                Arg("height", "Number"),
                Arg("radialSegments", "Integer"),
                Arg("heightSegments", "Integer"),
                Arg("thetaStart", "Number"),
                Arg("thetaLength", "Number"),
            ],
        )
    elif fi.name == "SphereGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("radius", "Number"),
                Arg("widthSegments", "Integer"),
                Arg("heightSegments", "Integer"),
                Arg("phiStart", "Number"),
                Arg("phiLength", "Number"),
                Arg("thetaStart", "Number"),
                Arg("thetaLength", "Number"),
            ],
        )
    elif fi.name == "CapsuleGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("radius", "Number"),
                Arg("length", "Number"),
                Arg("capSegments", "Integer"),
                Arg("radialSegments", "Integer"),
            ],
        )
    elif fi.name == "IcosahedronGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[], vals=[Arg("radius", "Number"), Arg("detail", "Integer")]
        )
    elif fi.name == "TorusGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("radius", "Number"),
                Arg("tube", "Number"),
                Arg("radialSegments", "Integer"),
                Arg("tubularSegments", "Integer"),
                Arg("arc", "Number"),
            ],
        )
    elif fi.name == "RingGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("innerRadius", "Number"),
                Arg("outerRadius", "Number"),
                Arg("thetaSegments", "Integer"),
                Arg("phiSegments", "Integer"),
                Arg("thetaStart", "Number"),
                Arg("thetaLength", "Number"),
            ],
        )
    elif fi.name == "OctahedronGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("radius", "Number"),
                Arg("detail", "Integer"),
            ],
        )
    elif fi.name == "PolyhedronGeometry":
        # parameters
        fi.properties[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("vertices", "OneOrMinusOne"),
                Arg("indices", ArrayArg("Integer")),
                Arg("radius", "Number"),
                Arg("detail", "Integer"),
            ],
        )
    elif fi.name == "LoadingManager":
        # addHandler regex
        fi.methods[0].args[0].tp = "Regex"
    elif fi.name == "MaterialLoader":
        # textures
        fi.properties[0].tp = RecordArg(val="Texture")
        # parse json
        fi.methods[1].args[0].tp = "JSON"
        # setTextures textures
        fi.methods[2].args[0].tp = RecordArg(val="Texture")
    elif fi.name == "Loader":
        # requestHeader
        fi.properties[5].tp = RecordArg(val="String")
        # setRequestHeader requestHeader
        fi.methods[7].args[0].tp = RecordArg(val="String")
    elif fi.name == "ImageBitmapLoader":
        # setOptions options
        fi.methods[1].args[0].tp = ObjectArg(
            optionals=[],
            vals=[
                Arg("imageOrientation", "ImageOrientation"),
                Arg("premultiplyAlpha", "PremultiplyAlpha"),
                Arg("colorSpaceConversion", "ColorSpaceConversion"),
                Arg("resizeWidth", "Integer"),
                Arg("resizeHeight", "Integer"),
                Arg("resizeQuality", "ResizeQuality"),
            ],
        )
    # elif fi.name == "Cache":
    #     # files
    #     fi.properties[1].tp = PLACEHOLDER
    #     # add file
    #     fi.methods[0].args[1].tp = PLACEHOLDER
    elif fi.name == "BufferGeometryLoader":
        # parse json
        fi.methods[1].args[0].tp = "JSON"
    elif fi.name == "DirectionalLightHelper":
        # matrix
        fi.properties[2].tp = "Matrix4"
        # matrixAutoUpdate
        fi.properties[3].tp = "Boolean"
    elif fi.name == "SpotLightHelper":
        # matrix
        fi.properties[2].tp = "Matrix4"
        # matrixAutoUpdate
        fi.properties[3].tp = "Boolean"
    elif fi.name == "CameraHelper":
        # pointMap
        fi.properties[1].tp = RecordArg(val="Integer")
        # matrix
        fi.properties[2].tp = "Matrix4"
        # matrixAutoUpdate
        fi.properties[3].tp = "Boolean"
    elif fi.name == "PointLightHelper":
        # matrix
        fi.properties[1].tp = "Matrix4"
        # matrixAutoUpdate
        fi.properties[2].tp = "Boolean"
    elif fi.name == "HemisphereLightHelper":
        # matrix
        fi.properties[1].tp = "Matrix4"
        # matrixAutoUpdate
        fi.properties[2].tp = "Boolean"
    elif fi.name == "Light":
        # toJSON meta
        fi.methods[2].args[0].tp = "Foreign"
    elif fi.name == "Curve":
        # fromJSON json
        fi.methods[14].args[0].tp = "JSON"

CHECKING2 = "Object"
for run in [True]:

    def rprint(*args):
        if run:
            directives.append(args)

    for fi in FILES:
        # logic for array replacement
        ####
        if fi.ctor is not None:
            for i in range(len(fi.ctor.args)):
                arg = fi.ctor.args[i]
                if arg.tp == CHECKING2:
                    rprint(fi.name, "CTOR", fi.ctor.args[i].name, arg, i)
        if fi.properties is not None:
            for i in range(len(fi.properties)):
                prop_ = fi.properties[i]
                prop = prop_
                if prop.tp == CHECKING2:
                    rprint(fi.name, "PROP", prop_.name, prop, i)
        if fi.methods is not None:
            for i in range(len(fi.methods)):
                method = fi.methods[i]
                if method.retval == CHECKING2:
                    rprint(fi.name, "RETVAL", method.name, i)
                for j in range(len(method.args)):
                    arg = method.args[j]
                    arg = arg
                    if arg.tp == CHECKING2:
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
for directive in directives:
    if directive[0] != FILENAME:
        FILENAME = directive[0]
        print(f'elif fi.name == "{FILENAME}":')
    if directive[1] == "CTOR":
        print(f"    # {directive[2]}")
        print(f"    fi.ctor.args[{directive[4]}].tp = PLACEHOLDER")
    elif directive[1] == "PROP":
        print(f"    # {directive[2]}")
        print(f"    fi.properties[{directive[4]}].tp = PLACEHOLDER")
    elif directive[1] == "RETVAL":
        print(f"    # {directive[2]} RETVAL")
        print(f"    fi.methods[{directive[3]}].retval = PLACEHOLDER")
    elif directive[1] == "METHOD":
        print(f"    # {directive[2]} {directive[5]}")
        print(f"    fi.methods[{directive[4]}].args[{directive[6]}].tp = PLACEHOLDER")

if __name__ == "__main__":
    import dataclasses
    import json

    class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            if o == FileType.CONSTANTS:
                return "CONSTANTS"
            if o == FileType.CLASS:
                return "CLASS"
            # print(o)
            return super().default(o)

    # for fi in FILES: print(fi)
    import sys

    sys.setrecursionlimit(10000)
    # print(json.dumps(FILES, cls=EnhancedJSONEncoder, indent=2))

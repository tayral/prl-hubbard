# -*- coding: utf-8 -*-

"""
@namespace  qat.core.magic.magic
@authors    Arnaud Gazda <arnaud.gazda@atos.net>
@copyright  2019 Bull S.A.S. - All rights reserved
            This is not Free or Open Source software.
            Please contact Bull SAS for details about its license.
            Bull - Rue Jean Jaurès - B.P. 68 - 78340 Les Clayes-sous-Bois

Description ...

Overview
========
"""
# Global imports
import time
import json
import math
import logging
import argparse
import tempfile as tmpf
from distutils.spawn import find_executable
from collections import OrderedDict
from decimal import Decimal
from qat.comm.datamodel.ttypes import OpType
from qat.comm.datamodel.ttypes import Circuit as TCircuit
from .svg import circ_to_svg
from ..printer import toPdf, pdf2png, InvalidOperation
from ..wrappers import Circuit
from ..variables import ArithExpression
from ..circuit_iterator import ops_iterate

# Import IPython
try:
    from IPython.core.magic import Magics, magics_class, line_cell_magic

except ModuleNotFoundError as err:
    raise RuntimeError(
        'Cannot import module "IPython", please ensure '
        'module "jupyter" is installed. To install jupyter, '
        "you can type the following command: "
        '"pip install jupyter"'
    ) from err

# Init logger
_LOGGER = logging.getLogger("qat.core.magic")


# Create magics
@magics_class
class QAT(Magics):
    """
    Jupyter Notebook Magics for Quantum Application toolset
    """

    # Magic qat display
    def plot(self, circuit, depth, filename=None):
        """
        Plot a circ file

        Args:
            circuit: a circuit
            depth: maximum depth of inlining
            filename (string, optional): the filename to print circuit to

        Returns:
            None
        """
        if not isinstance(circuit, Circuit):
            circuit = Circuit.from_thrift(circuit)

        # Init temporary name
        tmp_pdf_filename_radix = str()

        if filename is not None and not filename.endswith(".pdf"):
            raise ValueError(f"Filename must end with *.pdf, got {filename}")

        try:
            # Create a temporary PDF file
            tmp_pdf_file = (tmpf.NamedTemporaryFile(prefix="qat2pdf_", suffix="_circ.pdf",
                                                    dir=".") if filename is None else open(filename, "wb+"))

            # Create context for PDF file and PNG file
            with tmp_pdf_file, tmpf.NamedTemporaryFile(prefix="qat2pdf_", suffix="_circ.png", dir=".") as tmp_png_image:
                # Create PDF file
                tmp_pdf_filename_radix = tmp_pdf_file.name[:-4]
                toPdf(circuit, tmp_pdf_file, depth=depth)
                tmp_pdf_file.seek(0)

                # Create PNG file
                pdf2png(
                    pdf_file_object=tmp_pdf_file,
                    png_file_object=tmp_png_image,
                )
                tmp_png_image.seek(0)

                # Display image
                self.shell.run_cell(
                    f"import IPython; IPython.display.Image({tmp_png_image.read()})",
                    store_history=False,
                )

        except BaseException:
            _LOGGER.exception("Circuit printer failed on file %s", tmp_pdf_filename_radix)
            raise

    def plot_svg(self, circuit, depth, filename):
        """
        Plot an SVG version of the file

        Args:
            circuit (:class:`qat.core.Circuit`): circuit to plot
            depth (int): inline depth
        """
        # Display image
        svg = circ_to_svg(circuit, name=filename, max_depth=depth)
        self.shell.run_cell(
            f"import IPython; IPython.display.HTML('''{svg}''')",
            store_history=False,
        )

    def cell2circ(self, cell):
        """
        AQASM string to circuit
        """
        # Define the source and executable filenames.
        with tmpf.NamedTemporaryFile(suffix=".aqasm") as tmp_file_aq, tmpf.NamedTemporaryFile(suffix=".circ") as tmp_file_ci:
            tmp_name_aq = tmp_file_aq.name
            tmp_name_ci = tmp_file_ci.name

            # Write the code contained in the cell to the .aqasm file.
            with open(tmp_name_aq, "w") as file_:
                file_.write(cell)

            # Compile the AQASM code into a .circ file
            cmd = f"aqasm2circ {tmp_name_aq:s} {tmp_name_ci:s}"
            self.shell.system(cmd)
            return Circuit.load(tmp_name_ci)

    def print_hardware(self, circuit, hardware_model, filename=None):
        """
        Display a time plot using the hardware model. This function
        is not available for myQLM.

        Args:
            circuit (Circuit): circuit
            hardware_model (HardwareModel): hardware model
            filename (str, optional): file to print circuit to
        """
        # pylint: disable=no-self-use
        try:
            from qat.noisy.plot import (
                time_plot_advanced,
            )  # pylint: disable=import-outside-toplevel

            time_plot_advanced(circuit, hardware_model, filename)
        except ImportError as excp:
            raise NotImplementedError(
                "myQLM cannot display circuits using the " "hardware model. Please use a QLM to " "display the circuit"
            ) from excp

    @line_cell_magic
    def qatdisplay(self, line, cell=None):
        """
        Magic function to display a circuit
        """
        if cell is None:
            parser = argparse.ArgumentParser()
            parser.add_argument(
                "circuit",
                type=str,
                metavar="OBJECTNAME",
                help="OBJECT containing the " "circuit (or QRoutine) to be displayed",
            )

            parser.add_argument(
                "--hardware",
                "-hw",
                type=str,
                nargs=1,
                default=[None],
                help="OBJECT containing the hardware " "model (optional argument)",
            )

            parser.add_argument(
                "--depth",
                "-d",
                nargs="?",
                default=0,
                type=int,
                help="Maximum depth of inlining",
            )

            parser.add_argument("--svg", action="store_true", default=False, help="SVG display")

            parser.add_argument("--pdf", action="store_true", default=False, help="PDF display")

            parser.add_argument(
                "--file",
                "-f",
                type=str,
                default=[None],
                nargs=1,
                help="Name of file to print circuit to",
            )

            args = parser.parse_args(line.split())
            circuit = self.shell.user_ns[args.circuit]
            hardware_model = self.shell.user_ns[args.hardware[0]] if args.hardware[0] is not None else None
            depth = args.depth
            svg = args.svg
            force_pdf = args.pdf
            filename = args.file[0]

            # Cast circuit if the circuit is not a circuit
            if not isinstance(circuit, (TCircuit, Circuit)):
                # If the object is a Routine (workaround in order to avoid loading QRoutine)
                if "QRoutine" in str(type(circuit)) or "Gate" in str(type(circuit)):
                    from qat.lang.AQASM import (
                        Program,
                    )  # pylint: disable=import-outside-toplevel

                    prog = Program()
                    prog.apply(circuit, prog.qalloc(circuit.arity))
                    circuit = prog.to_circ(include_matrices=False)
                elif "Schedule" in str(type(circuit)):
                    from ..wrappers.schedule import (
                        plot_schedule,
                    )  # pylint: disable=import-outside-toplevel

                    plot_schedule(circuit, filename=filename)
                    return

            # Print circuit using hardware model
            if hardware_model is not None:
                self.print_hardware(circuit, hardware_model, filename)
                return

        else:
            circuit = self.cell2circ(cell)
            depth = 0

        # Print circuit
        if not svg and not self._force_svg_display():
            # Try to display the circuit using PDF renderer
            try:
                self.plot(circuit, depth, filename)

            # Catch exception raised if pdflatex does not work
            except (RuntimeError, InvalidOperation):
                if not force_pdf:
                    self._warn_pdf_not_working()
                    self.plot_svg(circuit, depth, filename)

                else:
                    raise

        else:
            self.plot_svg(circuit, depth, filename)

    def _warn_pdf_not_working(self):
        """
        Display a warning message saying that the SVG
        display is not working
        """
        self.shell.run_cell(
            r"""
            RuntimeWarning("The PDF display is not working. Please use "
                           "the \"--pdf\" option to display the error "
                           "message or use the \"--svg\" option to remove "
                           "this warning")
            """
        )

    def _force_svg_display(self):
        """
        Checks if the circuit must be displayed in SVG.
        If the command "pdflatex" is not installed on the
        device, SVG display will be used

        Returns:
            bool
        """
        # If pdflatex is not installed: force SVG display
        if find_executable("pdflatex") is None:
            # Print warning in the output cell of the user
            self.shell.run_cell(
                r"""
                RuntimeWarning("Command \"pdflatex\" is not installed. The circuit "
                               "will be displayed in SVG. (Please use \"--svg\" "
                               "option to remove this warning)")
                """,
                store_history=False,
            )
            return True

        # Otherwise: do not force SVG display
        return False

    #
    # JSQATDISPLAY
    #

    def d3plot(self, circuit, scale, extended, depth):
        """
        Display a circuit using D3 JS Library

        Args:
            circuit (Circuit): the circuit to display
            scale (float): scale
            extended (bool): if False, the circuit is contracted
            depth (int): maximum depth of inlining
        """
        for script in _jsscript_iterator(circuit, scale, extended, depth):
            self.shell.run_cell(script, store_history=False)

    @line_cell_magic
    def jsqatdisplay(self, line="", cell=None):
        """
        Gets the Circuit object on the line, parses it, then calls the
        function (cf. d3plot()) managing the JS script that prettily displays
        the circuit

        Args:
            line (str): the content of the line on which the magic is called
            cell (NoneType): the current cell, supposed to be empty

        Note:
            Calls the d3plot() function
        """
        # Setting the parser
        parser = argparse.ArgumentParser()

        # Getting the first parameter as the name of the variable containing
        # the circuit
        if cell is None:
            parser.add_argument(
                "circuit",
                type=str,
                metavar="OBJECTNAME",
                help="Object containing the circuit to be displayed",
            )

        # Setting of the optional scale parameter of the circuit display
        parser.add_argument(
            "--scale",
            "-sc",
            nargs="?",
            default=1.0,
            type=float,
            help="Scale of the circuit display",
        )

        # Setting og the optional depth parameter
        parser.add_argument(
            "--depth",
            "-d",
            nargs="?",
            default=0,
            type=int,
            help="Maximum depth of inlining",
        )

        # Setting the optional parameter that, if invoked, would extend the
        # display, rather than compressing it for visual convenience
        parser.add_argument(
            "--extended",
            "-ext",
            action="store_true",
            help="Whether the circuit must be extended or not (bool)",
        )

        # Getting the inputs
        args = parser.parse_args(line.split())

        # Get circuit
        circuit = None

        if cell is None:
            # Asserting the circuit is not None
            try:
                circuit = self.shell.user_ns[args.circuit]
            except Exception as exc:
                raise TypeError("The circuit must not be None") from exc

        else:
            circuit = self.cell2circ(cell)

        # Assigning the inputs into Python variables
        scale = args.scale
        extended = args.extended
        depth = args.depth

        # The circuit will not be displayed if `scale` is negative
        if scale < 0:
            scale = 1

        # Loading the py_d3 magic before calling the display function
        self.shell.run_cell("%%capture\n%load_ext qat.core.magic.py_d3", store_history=False)

        if circuit.nbqbits > 0:
            self.d3plot(circuit, scale, extended, depth)


# Util for JSQATDISPLAY
def _jsscript_iterator(circuit, scale, extended, depth):
    """
    First gets the data needed from the circuit through the circ_as_dict()
    function, then calls the right functions available via the custom.js
    file that prettily plot the circuit.

    Args:
        circuit (:obj:`qat.comm.datamodel.ttypes.Circuit`): the circuit
        scale (float): the circuit display scale
        extended (bool): if the circuit must be extended or not; by
            default, it is displayed compressed
        depth (int): maximum depth of inlining

    Note:
        Calls the circ_as_dict() function
    """

    # Asserting the circuit is not None
    try:
        circuit.ops
    except Exception as exc:
        raise TypeError("The circuit must not be None") from exc

    # Initialization of the number of slices per chunk of display
    slices_per_chunk = 50

    # Initialization of the JS equivalent to `extended`
    if extended:
        js_extended = "1"
    else:
        js_extended = "0"

    # Getting the data you need from the circuit as a Python OrderedDict
    # object, convertible to a json variable; calls the right function
    # if the display must be compressed or not
    data = json.dumps(_circ_as_dict(circuit, extended, depth))

    # Actual D3 script, requiring the D3 magic, initializing the circuit
    # by calling the right functions available via the custom.js file
    script = (
        """%%qatd3

    <table id="circuit"></table>

    <button id="svg_button">SVG export</button>

    <div id="svg_wrapper" hidden></div>

    <script>
        set_environment("""
        + data
        + """, """
        + str(scale)
        + """);
        init_display();
    </script>"""
    )

    # Running the script above as if it was the content of the cell itself
    yield script

    # Getting the list of every slices (the result of circ_as_dict()
    # without its first element, i.e. the circuit number of qubits)
    slices_list = list(_circ_as_dict(circuit, extended, depth).items())[1:]
    slices_list = [x[1] for x in slices_list]

    # Special case where the circuit has no operator; setting up the list
    # so only the qubits will be displayed
    if not slices_list:
        slices_list.extend([[{"gate": "NO_OP"}]])

    # Here, you'll chunk your display by displaying groups of slices one
    # after the other; note that all the try/catch JS blocks are to
    # prevent the display of ugly JS errors when the user refreshes the
    # notebook

    # Number of chunks through which you'll loop the call of the function
    # generating the circuit chunks
    chunks_nb = math.ceil(len(slices_list) / slices_per_chunk)

    # Loop through which you'll generate all the other chunks of display
    for k in range(chunks_nb):
        # Initialization of the slices list of the current state of the
        # loop
        chunk = slices_list[(slices_per_chunk * k): (slices_per_chunk * (k + 1))]
        # Conversion of the `chunk` list to a json string
        json_chunk = json.dumps(chunk)
        # Calling the function generating the chunk
        script = (
            """%%javascript
        try {
            generate_chunk_slices(
                """
            + json_chunk
            + """, """
            + str(k)
            + """
            );\n"""
        )
        # Initializing the animations for the first chunk displayed
        if k == 0:
            script += (
                """init_animations(width, """
                + js_extended
                + """);
            } catch (err) {
                $("#svg_button").closest(".output_area").remove();
                $(".js-error").remove();
            }
            """
            )
        else:
            script += """} catch (err) { }\n"""
        # Removing the debris div.output_area element that would appear to
        # leave a thin blank space
        script += """$(".output_area:not(:first-child)").remove();"""
        # Executing the script
        yield script
        # Break to let the chunk be generated; it has been empirically
        # shown that this smoothes the display time and reduces the
        # browser struggle to display huge circuits (e.g. with 1e4 gates)
        time.sleep(0.5)
    # Initializing the animations for the generated chunks along with the
    # svg-print button
    script = (
        """%%javascript
    try {
        init_animations(width, """
        + js_extended
        + """);
        init_svg_print("""
        + data
        + """, width, """
        + js_extended
        + """);
    } catch (err) {
        console.log("The error blocking the display is: " + err)
    }\n"""
    )
    # Removing the debris div.output_area element that would appear to
    # leave a thin blank space
    script += """$(".output_area:not(:first-child)").remove();"""
    # Executing the script
    yield script


def _circ_as_dict(circuit, extended, depth):
    """
    Stores the needed data from a quantum circuit to a json-able
    OrderedDict, with the circuit number of qubits, and every slices, a
    slice being a group of gates displayed vertically; each slice gate is
    characterized by:
     - ctrl: the number of control qubits of the gate
     - dag: 1 if a dagger is applied on the gate, 0 otherwise
     - gate: the name of the gate
     - index: the gate index
     - params: its parameters, as a list of str objects (empty if the
       gate has none)
     - qbits: the list of every qubits the gate is applied on

    Args:
        circuit (:obj:`qat.comm.datamodel.ttypes.Circuit`): the circuit
        extended (bool): if the circuit must be extended or not; by
            default, it is displayed compressed
        depth (int): maximum depth of inlining

    Returns:
        dic (:obj:`OrderedDict`): the ordered dictionary containing all
            needed information

    Note:
        Calls the following functions:
         - get_slices()
         - double_format()
         - matrix_as_list()
         - dag_or_ctrl()
    """
    # Asserting the circuit is not None
    try:
        circuit.ops
    except Exception as exc:
        raise TypeError("The circuit must not be None") from exc

    # Getting the list of every vertical slices (containing as many gates
    # as possible) of the circuit, converted from sets to lists
    slices = [list(item) for item in _get_slices(circuit, extended, depth)]

    # Initialization of the return variable with the circuit number of
    # qubits, as an nstante of an OrderedDict instead of a dict, because
    # both are json-able, but a built-in dict would have issues about the
    # operators order (e.g. the 1000th operator would be before the 2nd).
    dic = OrderedDict([("nbqbits", circuit.nbqbits)])

    # Loop for each circuit slice
    for slice_index, cur_slice in enumerate(slices):
        # Initialization of the slice gates list
        slice_list = []

        # Loop for each gate of the current slice
        for cur_gate in cur_slice:
            # Initializing the gate data object as a dictionary
            gate_dict = {"index": cur_gate[2], "qbits": cur_gate[1]}

            # If REMAP:
            if cur_gate[0] == "-REMAP-":
                # Init dag and
                gate_dict["ctrl"], gate_dict["dag"] = 0, 0

                # Set gate and name
                gate_dict["gate"] = "-REMAP-"

                # Set remap
                gate_dict["params"] = [str(qb) for qb in cur_gate[3]]

                # Add in slice_list
                slice_list.extend([gate_dict])

                # Go to the top of for loop
                continue

            # Getting the current gate gateDic Python object
            gate_def = circuit.gateDic[cur_gate[0]]

            # Getting the current gate syntax Python object, along with
            # the gate number of qubits and if a dagger is applied on it
            syntax, gate_dict["ctrl"], gate_dict["dag"] = _dag_or_ctrl(circuit, gate_def)

            # Getting the name of the gate
            gate_dict["gate"] = syntax.name

            # Correcting the value of the `ctrl` key for CNOT and
            # CCNOT gates
            if gate_dict["gate"] == "CNOT":
                gate_dict["ctrl"] += 1
            elif gate_dict["gate"] == "CCNOT":
                gate_dict["ctrl"] += 2

            # Adding the gate matrix in the dictionary, if it actually
            # has one (it sometimes doesn't)
            if circuit.gateDic[cur_gate[0]].matrix is not None:
                gate_dict["matrix"] = _matrix_as_list(circuit, gate_def)

            # Getting the parameters of the gate, as a list of str
            # objects
            params = []
            for syntax_param in syntax.parameters:
                if syntax_param.is_abstract:
                    params.extend([str(ArithExpression.from_string(syntax_param.string_p))])
                elif syntax_param.type == 0:
                    params.extend([str(syntax_param.int_p)])
                elif syntax_param.type == 1:
                    params.extend([_double_format(syntax_param.double_p, list(dic.items())[0][1])])
                elif syntax_param.type == 2:
                    params.extend([syntax_param.string_p])
            gate_dict["params"] = params

            # Adding the gate to the slice
            slice_list.extend([gate_dict])

        # Adding the operator in the dictionary
        dic.update({"slice-" + str(slice_index): slice_list})

    return dic


def _get_gate_name(operator):
    """
    Returns operator.gate if the gate attribute is defined
    Returns "-REMAP-" if the gate is a REMAP gate

    Args:
        operator (Op)

    Returns:
        str: gate name
    """
    # Try to find a name
    if operator.gate is not None:
        return operator.gate

    if operator.type == OpType.REMAP:
        return "-REMAP-"

    # Except: raise error
    raise ValueError("Magic jsqatdisplay can only display circuits " "composed of GATETYPE operators")


def _get_slices(circuit, extended, depth):
    """
    Yields a set for every slice of the circuit (corresponding to a
    vertical slice of circuit containing as many gates as possible).

    Args:
        circuit (:obj:`qat.comm.datamodel.ttypes.Circuit`): the circuit
        extended (bool): if the circuit must be extended or not; by
            default, it is displayed compressed
        depth (int): maximum depth of inlining

    Returns:
        (generator): a generator of every sets containing every gates for
            each slice
    """

    # Asserting the circuit is not None
    if circuit is None:
        raise TypeError("The circuit must not be None")

    # Credits to the real Arnaud Gazda <arnaud.gazda@atos.net>

    # If the circuit must be displayed with a single gate per slice
    if extended:
        # Returns a slice which contains only one gate
        for index, operator in enumerate(ops_iterate(circuit, False, depth)):
            yield {
                (
                    _get_gate_name(operator),
                    tuple(operator.qbits),
                    index,
                    tuple(operator.remap) if operator.remap else operator.remap,
                )
            }

        return

    # If the circuit must be displayed with multiple gates per slice
    # (default behavior)

    # List of op for a given qubits
    # qubits[qb][slice] == op, index
    qubits = [[] for _ in range(circuit.nbqbits)]

    # For each op
    for index, operator in enumerate(ops_iterate(circuit, False, depth)):

        # Getting the first and the last qubits on which the gate is
        # applied
        first_qb = min(operator.qbits)
        last_qb = max(operator.qbits)

        # Getting the slice on which the gate will be set
        current_slice = max(len(qubits[qb]) for qb in range(first_qb, last_qb + 1))

        # Complete the qubits with `None` to have the same lists length
        for qbit in range(first_qb, last_qb + 1):
            while len(qubits[qbit]) < current_slice:
                qubits[qbit].append(None)

            # Apply the op to the list
            qubits[qbit].append((operator, index))

    # Getting the depth of the circuit
    depth = max(len(qubits[qb]) for qb in range(circuit.nbqbits))

    # Generating each slice as a set containing:
    #  - the name of the gate
    #  - a tuple containing every qubits on which the gate is applied
    #  - the gate index
    for current_slice in range(depth):
        gate_applied = set()
        for qbit in range(circuit.nbqbits):
            is_current_slice = len(qubits[qbit]) > current_slice
            if is_current_slice and qubits[qbit][current_slice] is not None:
                operator = qubits[qbit][current_slice][0]
                index = qubits[qbit][current_slice][1]
                gate_applied.add(
                    (
                        _get_gate_name(operator),
                        tuple(operator.qbits),
                        index,
                        tuple(operator.remap) if operator.remap else operator.remap,
                    )
                )

        yield gate_applied


def _dag_or_ctrl(circuit, gate_def, count=0, is_dag=0):
    """
    Recursive function to be called if a gateDic has no syntax, meaning
    it is a (possibly multiple) controlled gate or/and that a dagger is
    applied on it.

    Args:
        circuit (:obj:`qat.comm.datamodel.ttypes.Circuit`): the circuit
        gate_def (:obj:`qat.comm.datamodel.ttypes.GateDefinition`): the
            gate definition object
        count (int, optional): the control qubits counter
        is_dag (int, optional): 1 if a dagger is applied on the gate, 0
            otherwise

    Returns:
        (:obj:`qat.comm.datamodel.ttypes.GSyntax`): the standard gate
            syntax object
        count (int): the number of control qubits applied
        is_dag (int): 1 if a dagger is applied on the gate, 0 otherwise
    """
    # Asserting the circuit is not None
    try:
        circuit.ops
    except Exception as exc:
        raise TypeError("The circuit must not be None") from exc
    # The choice of a number instead of a boolean for `is_dag` is because
    # there would be issues with the `true` or `false` values while
    # converting the circ_as_dict() OrderedDict to a json string
    if gate_def.syntax is not None:
        return gate_def.syntax, count, is_dag

    if gate_def.is_dag is True:
        is_dag = 1
    elif gate_def.nbctrls is not None:
        count += gate_def.nbctrls
    elif gate_def.is_ctrl is True:
        count += 1
    gate_def = circuit.gateDic[gate_def.subgate]
    return _dag_or_ctrl(circuit, gate_def, count, is_dag)


def _double_format(num, nb_qbits):
    """
    Gets a real number to return this one with four digits after the
    decimal point, or as a fraction of pi, if it actually is one.

    Args:
        num (float): the number to check
        nbQbits (int): the circuit number of qubits

    Returns:
        checked (str): the number as a fraction of pi if it is one,
            otherwise itself with four digits after the decimal point
    """
    # Initializing the return variable as the input number as a string,
    # truncated if it has more than four digits after the decimal point
    if abs(Decimal(str(num)).as_tuple().exponent) > 4:
        checked = f"{num:.4f}"
    else:
        checked = str(num)
    # Epsilon, your precision variable, to check if the input number is
    # comparable to a fraction of pi
    eps = 1e-5
    # Comparing the paramater to pi
    if abs(abs(num) - math.pi) < eps:
        if num < 0:
            checked = "-π"
        else:
            checked = "π"
    # Comparing the parameter to a division of pi by an exponent of 2
    else:
        division = math.pi / 2
        for k in range(1, nb_qbits):
            if abs(abs(num) - division) < eps:
                if num < 0:
                    checked = "-π/" + str(2**k)
                else:
                    checked = "π/" + str(2**k)
                break
            division /= 2
    return checked


def _matrix_as_list(circuit, gate_def):
    """
    Returns the matrix of the lowest level gate (the one with no control
    qubits) as a list of lists of str objects, in the form of `a + bi`
    where `a` is the real part of the number represented, and `b` is its
    imaginary one.
    If b≈0, the object is in the form of `a`; if a≈0, the object is in
    the form of `bi`. The statement `roughly equal` is arbitrarly set to
    an approximation of 1e-3.
    If |b|=1, `i` is displayed alone, instead of in the form of `±1.00i`.
    The number of digits after the decimal point is set to two.

    Args:
        circuit (:obj:`qat.comm.datamodel.ttypes.Circuit`): the circuit
        gate_def (:obj:`qat.comm.datamodel.ttypes.GateDefinition`): the
            gate definition object

    Returns:
        the_matrix (list): the matrix as a list of lists of strings

    Note:
        Calls the get_subgate_matrix() function
    """

    # Asserting the circuit is not None
    try:
        circuit.ops
    except Exception as exc:
        raise TypeError("The circuit must not be None") from exc

    # Return variable
    the_matrix = []

    # Getting the matrix object of the lowest level gate, the one with no
    # control qubits
    matrix = _get_subgate_matrix(circuit, gate_def)

    # This one counter is to get the right element of the matrix data
    data_count = 0
    # Loop for each row of the matrix
    for _row in range(matrix.nRows):
        row = []
        # Loop for each element of the row
        for _col in range(matrix.nCols):
            # Getting the real and imaginary parts of the element
            real = matrix.data[data_count].re
            imag = matrix.data[data_count].im
            # Case imag≈0 => displaying `real`
            if abs(imag) < 1e-3:
                num = f"{real:.2f}"
            # Case real≈0 => displaying `imag i`
            elif abs(real) < 1e-3:
                # Displaying `±i` if |imag|=1
                if abs(imag) == 1:
                    num = "i" if imag > 0 else "-i"
                # Else displaying `bi`
                else:
                    num = f"{imag:.2f}i"
            # Case real≠0 and imag≠0 => displaying `real ± |imag|i`
            else:
                # Instantiate with `real`
                num = f"{real:.2f}"
                # Adding `±i` if |imag|=1
                if abs(imag) == 1:
                    num += " + i" if imag > 0 else " - i"
                # Adding ` ± |imag|i` if |imag|≠1
                else:
                    num += " + " if imag > 0 else " - "
                    num += f"{abs(imag):.2f}i"
            # Adding the element to the row elements list
            row.append(num)
            # Incrementing the matrix.data counter
            data_count += 1
        # Adding the row to the matrix rows list
        the_matrix.append(row)
    return the_matrix


def _get_subgate_matrix(circuit, gate_def):
    """
    Recursive function that returns the matrix object of the lowest level
    gate, i.e. the one with no control qubits.

    Args:
        circuit (:obj:`qat.comm.datamodel.ttypes.Circuit`): the circuit
        gate_def (:obj:`qat.comm.datamodel.ttypes.GateDefinition`): the
            gate definition object

    Returns:
        (:obj:`qat.comm.datamodel.ttypes.Matrix`): the gate matrix object
    """
    # Asserting the circuit is not None
    try:
        circuit.ops
    except Exception as exc:
        raise TypeError("The circuit must not be None") from exc

    # Recursive part
    if gate_def.subgate is None:
        return gate_def.matrix

    gate_def = circuit.gateDic[gate_def.subgate]
    return _get_subgate_matrix(circuit, gate_def)


# Install magics
def load_ipython_extension(ipython):
    """
    Any module file that define a function named `load_ipython_extension`
    can be loaded via `%load_ext module.path` or be configured to be
    autoloaded by IPython at startup time.
    """
    # You can register the class itself witouth instantiating it. IPython will
    # call the default constructor on it
    ipython.register_magics(QAT)

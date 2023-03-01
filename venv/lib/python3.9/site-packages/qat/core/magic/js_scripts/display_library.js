/**
 * @author Gabriel Proust <gabriel.proust@atos.net>
 * @version 1.3.0
 */


// Some built-in Array object enhancements.
Array.prototype.min = function() { return Math.min.apply(null, this); };
Array.prototype.max = function() { return Math.max.apply(null, this); };


/* ================================================================== */
/*      DATA TREATMENT AND CUSTOMIZATION                              */
/* ================================================================== */


/**
 * Sets the global variables, as the dimensions one, and the color one
 * (you can set it in the raw if you feel like having a blue or purple
 * display).
 *
 * @param {string} data - The JSON string containing all the needed data
 * @param {number} scale - The display scale
 */
function set_environment(data, scale) {

    // Extracting the number of qubits of the circuit from the data
    nbQbits = data.nbqbits;

    // Creation of the list of operators in data as a list of objects
    opsList = [];
    const dataCopy = JSON.parse(JSON.stringify(data));
    delete dataCopy["nbqbits"];
    for (let key in dataCopy) {
        opsList.push(dataCopy[key]);
    }

    // Setting the dimensions variables, with:
    //  - `width` the slices width
    //  - `height` the qubits space height
    //  - `padding` some small dimension mostly used to pad
    // The two last ones depend on `width`.
    width = 60 * scale;
    height = width * (2/3);
    padding = height/12;

    // The color you want the whole circuit to be in.
    color = "black";
}


/* ================================================================== */
/*      TOOLS TO BUILD A GATE                                         */
/* ================================================================== */


/**
 * Treats the `qbits` list so to get the elements you need for specific
 * tasks
 * 
 * @param {object} gateData - The current gate needed data
 * 
 * @return {Array} gate - The list of qubits on which the gate is
 *     applied
 * @return {number} length - The length of the gate, i.e. on how many
 *     qubits the rectangle embodying the gate will lay (even if the
 *     gate is not applied on some of them)
 * @return {Array} inn - The list of control qubits on which the gate
 *     lays, but on which the gate is not applied (if there are any)
 * @return {Array} ext - The list of control qubits that are not
 *     overlapped by the gate and linked to the gate by a line
 */
function qbits_list_treatment(gateData) {

    const gate = gateData.qbits.slice(gateData.ctrl);
    gate.sort();

    const length = gate.max() - gate.min() + 1;

    const inn = [];
    const ext = [];
    // `inn` will be filled only with the inner control qubits of the
    // gate, the ones that are between the first and last qubits of the
    // gate, and will stay empty if there are none;
    // `ext` will be filled with the other control qubits
    for (let k = 0; k < gateData.ctrl; k++) {
        const curQbit = gateData.qbits[k];
        if (gate.length > 1) {
            if (gate.min() < curQbit && curQbit < gate.max()) {
                inn.push(curQbit);
            } else {
                ext.push(curQbit);
            }
        } else {
            ext.push(curQbit);
        }
    }

    return [gate, length, inn, ext];
}

/**
 * Appends dots on the control qubits.
 * If some control qubits are not overlapped by the gate, adds a line
 * linking the dot to the gate with a white rectangle (to able the
 * trigger of the mouseenter and mouseleave events) beneath it.
 * 
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 */
function ctrl_qbits(gateContainer, gateData) {

    const dotRadius = width/12;

    // Treating the `qbits` list (cf. the qbits_list_treatment function)
    const treatment = qbits_list_treatment(gateData);
    const gate = treatment[0];
    const inn = treatment[2];
    const ext = treatment[3];

    // Addition of the rectangles whose role will be to able the trigger
    // of the mouseenter and mouseleave events, for the qubits that are
    // not overlapped by the gate
    if (ext.length > 0) {

        // Rectangle above the gate, if needed
        if (ext.min() < gate.min()) {
            gateContainer.append("rect")
                    .attr("x", width/9)
                    .attr("y", ext.min() * height)
                    .attr("width", width * (7/9))
                    .attr("height", (gate.min() - ext.min()) * height)
                    .attr("fill", "white");
        }

        // Rectangle below the gate, if needed
        if (gate.max() < ext.max()) {
            gateContainer.append("rect")
                    .attr("x", width/9)
                    .attr("y", (gate.max() + 1) * height)
                    .attr("width", width * (7/9))
                    .attr("height", (ext.max() - gate.max()) * height)
                    .attr("fill", "white");
        }
    }

    // Replacing the lines representing the qubits on the rectangles
    if (ext.min() < gate.min()) {
        for (let k = ext.min(); k < gate.min(); k++) {
            gateContainer.append("line")
                    .classed("qbit" + k, true)
                    .attr("x1", width/9)
                    .attr("x2", width * (8/9))
                    .attr("y1", ((2 * k + 1) * height) / 2)
                    .attr("y2", ((2 * k + 1) * height) / 2)
                    .attr("stroke", color)
                    .attr("stroke-width", width/70);
        }
    }
    if (ext.max() > gate.max()) {
        for (let k = gate.max() + 1; k <= ext.max(); k++) {
            gateContainer.append("line")
                    .classed("qbit" + k, true)
                    .attr("x1", width/9)
                    .attr("x2", width * (8/9))
                    .attr("y1", ((2 * k + 1) * height) / 2)
                    .attr("y2", ((2 * k + 1) * height) / 2)
                    .attr("stroke", color)
                    .attr("stroke-width", width/70);
        }
    }

    // Appending a line linking the two opposite qubits of the gate, if
    // there are control qubits that are external to the gate (the line
    // may be covered by other graphic elements)
    if (ext.length > 0) {
        gateContainer.append("line")
                .attr("x1", width/2)
                .attr("x2", width/2)
                .attr("y1", height * (2 * gateData.qbits.min() + 1) / 2)
                .attr("y2", height * (2 * gateData.qbits.max() + 1) / 2)
                .attr("stroke", color)
                .attr("stroke-width", width/70);
    }

    // Addition of the dots overlapped by the gate
    if (inn.length > 0) {
        for (let k = 0; k < inn.length; k++) {
            gateContainer.append("circle")
                    .classed("dot", true)
                    // If the gate is represented as a rectangle, the
                    // overlapped control qubits will be displaced
                    // at the right end of the rectangle; if not, it
                    // will be placed on the center vertical line
                    .attr("cx", function() {
                        const names = [
                            "CNOT",
                            "CCNOT",
                            "SWAP",
                            "CSIGN"
                        ];
                        if (names.includes(gateData.gate)) {
                            return width/2;
                        } else {
                            return width * (9/10);
                        }
                    })
                    .attr("cy", height * (2 * inn[k] + 1) / 2)
                    .attr("r", dotRadius)
                    .attr("fill", color);
        }
    }

    // Addition of any other dot, at some point of the vertical line
    for (let k = 0; k < ext.length; k++) {
        gateContainer.append("circle")
                .classed("dot", true)
                .attr("cx", width/2)
                .attr("cy", height * (2 * ext[k] + 1) / 2)
                .attr("r", dotRadius)
                .attr("fill", color);
    }
}

/**
 * Construction of a CNOT or CCNOT gate, as a dot on the controlled
 * qubit, a target (circle + line) on the targeted qubit, and a line
 * between the dot and the target.
 * 
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 */
function draw_cnot(gateContainer, gateData) {

    // Getting the list of the qubits on which the gate is applied,
    // without the control qubits
    const gate = qbits_list_treatment(gateData);

    // Addition of the rectangles whose role will be to able the trigger
    // of the mouseenter and mouseleave events, under the target
    gateContainer.append("rect")
            .attr("x", width/9)
            .attr("y", gate[0] * height)
            .attr("width", width * (7/9))
            .attr("height", height)
            .attr("fill", "white");

    // Replacement of the lines representing the qubits on the rectangle
    const name = "qbit" + gate[0];
    gateContainer.append("line")
            .classed(name, true)
            .attr("x1", width/9)
            .attr("x2", width * (8/9))
            .attr("y1", ((2 * gate[0] + 1) * height) / 2)
            .attr("y2", ((2 * gate[0] + 1) * height) / 2)
            .attr("stroke", color)
            .attr("stroke-width", width/70);

    // Construction of the target on the targeted qubit;
    const targeted = gate[0];
    // Circle of the targeted qubit
    gateContainer.append("circle")
            .classed("target-circle", true)
            .attr("cx", width/2)
            .attr("cy", height * (2 * targeted + 1) / 2)
            .attr("r", width/4)
            .attr("fill", "none")
            .attr("stroke", color)
            .attr("stroke-width", width/70);
    // Vertical line of the target
    gateContainer.append("line")
            .classed("target-line", true)
            .attr("x1", width/2)
            .attr("x2", width/2)
            .attr("y1", height * (2 * targeted + 1) / 2 - width/4)
            .attr("y2", height * (2 * targeted + 1) / 2 + width/4)
            .attr("stroke", color)
            .attr("stroke-width", width/70);

    // Addition of the control qubits and their line
    ctrl_qbits(gateContainer, gateData);
}

/**
 * Construction of a CSIGN gate, as two dots linked by a line.
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 */
function draw_csign(gateContainer, gateData) {

    const dotRadius = width/12;

    // Getting the list of the qubits on which the gate is applied,
    // without the control qubits, and the length of the gate (the
    // number of qubits on which its visualization will lay)
    const treatment = qbits_list_treatment(gateData);
    const gate = treatment[0];
    const length = treatment[1];

    // Addition of the rectangles whose role will be to able the trigger
    // of the mouseenter and mouseleave events
    gateContainer.append("rect")
            .attr("x", width/9)
            .attr("y", gate.min() * height)
            .attr("width", width * (7/9))
            .attr("height", (gate.max() - gate.min() + 1) * height)
            .attr("fill", "white");

    // Replacement of the lines representing the qubits on the rectangle
    for (let k = gate.min(); k <= gate.max(); k++) {

        gateContainer.append("line")
                .classed("qbit" + k, true)
                .attr("x1", width/9)
                .attr("x2", width * (8/9))
                .attr("y1", ((2 * k + 1) * height) / 2)
                .attr("y2", ((2 * k + 1) * height) / 2)
                .attr("stroke", color)
                .attr("stroke-width", width/70);

        // Addition of the dots on the two affected qubits
        if (gate.includes(k)) {
            gateContainer.append("circle")
                    .classed("dot", true)
                    .attr("cx", width/2)
                    .attr("cy", height * (2 * k + 1) / 2)
                    .attr("r", dotRadius)
                    .attr("fill", color);
        }
    }

    // Addition of the line linking the two dots
    gateContainer.append("line")
            .attr("x1", width/2)
            .attr("x2", width/2)
            .attr("y1", ((2 * gate[0] + 1) * height) / 2)
            .attr("y2", ((2 * gate[gate.length - 1] + 1) * height) / 2)
            .attr("stroke", color)
            .attr("stroke-width", width/70);
}

/**
 * Draws a SWAP gate, as two crosses on each qubit to treat, and a line
 * between each cross.
 *
 * This representation lays on a rectangle that aims to able the trigger
 * of the mouseenter and mouseleave events.
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 */
function draw_swap(gateContainer, gateData) {

    // Treatment of the `qbits` list
    const treatment = qbits_list_treatment(gateData);
    const gate = treatment[0];
    const length = treatment[1];

    // Addition of the rectangle whose role will be to make able to
    // trigger the mouseenter and mouseleave events
    gateContainer.append("rect")
            .attr("x", width/9)
            .attr("y", gate.min() * height)
            .attr("width", width * (7/9))
            .attr("height", length * height)
            .attr("fill", "white");
    // Replacement of the lines representing the qubits on the rectangle
    for (let k = gate.min(); k <= gate.max(); k++) {
        gateContainer.append("line")
                .classed("qbit" + k, true)
                .attr("x1", width/9)
                .attr("x2", width * (8/9))
                .attr("y1", ((2 * k + 1) * height) / 2)
                .attr("y2", ((2 * k + 1) * height) / 2)
                .attr("stroke", color)
                .attr("stroke-width", width/70);
    }

    // First part of the crosses
    for (let k = 0; k < gate.length; k++) {
        gateContainer.append("line")
                .classed("cross-0-"+k, true)
                .attr("x1", width * 3/8)
                .attr("x2", width * 5/8)
                .attr("y1", height * (2 * gate[k] + 1) / 2 - width/8)
                .attr("y2", height * (2 * gate[k] + 1) / 2 + width/8)
                .attr("stroke", color)
                .attr("stroke-width", width/70);
    }

    // Second part of the crosses
    for (let k = 0; k < gate.length; k++) {
        gateContainer.append("line")
                .classed("cross-1-"+k, true)
                .attr("x1", width * 3/8)
                .attr("x2", width * 5/8)
                .attr("y1", height * (2 * gate[k] + 1) / 2 + width/8)
                .attr("y2", height * (2 * gate[k] + 1) / 2 - width/8)
                .attr("stroke", color)
                .attr("stroke-width", width/70);
    }

    // Line linking the crosses
    gateContainer.append("line")
            .attr("x1", width/2)
            .attr("x2", width/2)
            .attr("y1", height * (2 * gate[0] + 1) / 2)
            .attr("y2", height * (2 * gate[1] + 1) / 2)
            .attr("stroke", color)
            .attr("stroke-width", width/70);
}

/*
 * Construction of a REMAP gate.
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 * */
function draw_remap(gateContainer, gateData) {

    // Get list of qubits
    const qbits = gateData.qbits;

    // Draw rectangle behind qubits (to hide qubits)
    gateContainer.append("rect")
            .attr("x", width/9)
            .attr("y", qbits.min() * height)
            .attr("width", width * (7/9))
            .attr("height", (qbits.max() - qbits.min() + 1) * height)
            .attr("fill", "white");

    // Draw line for each qubit
    for (let qb = qbits.min(); qb <= qbits.max(); qb++) {
        // If qubit not in remap
        if (qbits.indexOf(qb) == -1) {
            gateContainer.append("line")
                    .classed("qbits" + qb, true)
                    .attr("x1", width/9)
                    .attr("x2", width * (8/9))
                    .attr("y1", ((2 * qb + 1) * height) / 2)
                    .attr("y2", ((2 * qb + 1) * height) / 2)
                    .attr("stroke", color)
                    .attr("stroke-width", width/70);
        }

        // If qubit in remap
        else {
            let index_in = qbits.indexOf(qb);
            let index_out = gateData.params[index_in];
            let qb_out = qbits[index_out];

            gateContainer.append("line")
                    .classed("qbits" + qb, true)
                    .attr("x1", width/9)
                    .attr("x2", width * (8/9))
                    .attr("y1", ((2 * qb + 1) * height) / 2)
                    .attr("y2", ((2 * qb_out + 1) * height) / 2)
                    .attr("stroke", color)
                    .attr("stroke-width", width/70);
        }
    }
}

/**
 * Gets the list of parameters of the gate, and returns a string listing
 * the parameters, separated by commas.
 * If there are too many parameters, or they take too much room, the
 * list is limited to the two first parameters, followed by ellipsis.
 * Every parameters that are real numbers are formatted.
 *
 * @param {Array} params - The list of the gate parameters (as strings)
 * @return {string} display - The string to display
 */
function params_format(params) {

    /**
     * Function to check if the parameter has to be formated because
     * of being a real number.
     *
     * If it is, returns the right pi division if it actually is a
     * division of pi, otherwise returns the parameter with a maximum of
     * two digits after the decimal point.
     *
     * @param {string} param - The parameter to check
     * @return {string} checked - The parameter formatted if it is a
     *     real number, with a maximum of two digits after the decimal
     *     point
     */
    const format_if_float = function(param) {
        // Initializing the `checked` variable as the parameter itself,
        // as it will be returned unchanged if it is not a float number
        // or is one with less than three digits after the decimal point
        let checked = param;
        // If it is a real number and has more than two digits after the
        // decimal point, it will be formated
        const isLongFloat =
                Number(param) == param &&
                param % 1 != 0 &&
                param.split(".")[1].length > 2;
        if (isLongFloat) checked = parseFloat(param).toFixed(2);
        return checked;
    };

    // The return variable
    let display = format_if_float(params[0]);
    // Construction of the display as the list of every parameters
    // separated by commas
    for (let k = 1; k < params.length; k++) {
        display += ", " + format_if_float(params[k]);
    }
    // If the parameters take too much space, the display will be the
    // two first ones followed by ellipsis
    if (display.length > 9 && params.length > 2) {
        display =  format_if_float(params[0]) + ", " +
                format_if_float(params[1]) + ", ...";
    }

    return display;
}

/**
 * Construction of any kind of gate with a rectangle, whose size and
 * position depend on the qubits it is applied on, its name on the
 * middle of the rectangle, and its parameters in brackets if it has any
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 */
function draw_rect_gate(gateContainer, gateData) {

    // Treatment of the `qbits` list (cf. qbits_list_treatment)
    const treatment = qbits_list_treatment(gateData);
    const gate = treatment[0];
    const length = treatment[1];
    const inn = treatment[2];

    // List of every qubits that are not control ones and are overlapped
    // by the rectangle
    const overlapped = [];
    for (let k = gate.min(); k < gate.max(); k++) {
        if (!gate.includes(k) && !inn.includes(k)) {
            overlapped.push(k);
        }
    }

    // Special treatment for the qubits covered by the rectangle, on
    // which the gate is not applied, if there are any
    const hasParams = gateData.params.length > 0;
    if (length > gate.length) {
        // Loop for each affected qubits
        for (let k = 0; k < overlapped.length; k++) {
            // Appending a white rectangle on each side of the gate
            // to erase the qubit lines; there's a special operation
            // about the x attribute, because the width and the x origin
            // of the gate depends if it has parameters or not
            gateContainer.append("rect")   // The right one
                    .attr("x", function() {
                        if (hasParams) return width * (8/9);
                        else return width * (5/6);
                    })
                    .attr("y", (2 * overlapped[k] + 1) * height/2 -
                            width/15)
                    .attr("width", width/12)
                    .attr("height", width * (2/15))
                    .attr("fill", "white");
            gateContainer.append("rect")   // The left one
                    .attr("x", function() {
                        if (hasParams) return width * (1/9 - 1/15);
                        else return width * (1/6 - 1/15);
                    })
                    .attr("y", (2 * overlapped[k] + 1) * height/2 -
                            width/15)
                    .attr("width", width/15)
                    .attr("height", width * (2/15))
                    .attr("fill", "white");
            // Appending a small vertical line on each side of the
            // gate, to mark the fact that the gate is not applied
            // on this particular qubit
            gateContainer.append("line")   // The right one
                    .attr("x1", function() {
                        if (hasParams) return width * (8/9 + 1/15);
                        else return width * (5/6 + 1/15);
                    })
                    .attr("y1", (2 * overlapped[k] + 1) * height/2 -
                            width/15)
                    .attr("x2", function() {
                        if (hasParams) return width * (8/9 + 1/15);
                        else return width * (5/6 + 1/15);
                    })
                    .attr("y2", (2 * overlapped[k] + 1) * height/2 +
                            width/15)
                    .attr("stroke", color)
                    .attr("stroke-width", width/50);
            gateContainer.append("line")   // The wrong one (haha)
                    .attr("x1", function() {
                        if (hasParams) return width * (1/9 - 1/15);
                        else return width * (1/6 - 1/15);
                    })
                    .attr("y1", (2 * overlapped[k] + 1) * height/2 -
                            width/15)
                    .attr("x2", function() {
                        if (hasParams) return width * (1/9 - 1/15);
                        else return width * (1/6 - 1/15);
                    })
                    .attr("y2", (2 * overlapped[k] + 1) * height/2 +
                            width/15)
                    .attr("stroke", color)
                    .attr("stroke-width", width/50);
        }
    }

    // Construction of the rectangle modelizing the gate, at the right
    // size (depending on how many qubits it lays on), a bit wider if
    // the gate has parameters
    gateContainer.append("rect")
            .classed("gate", true)
            .attr("x", function() {
                if (hasParams) return width/9;
                else return width/6;
            })
            .attr("y", gate.min() * height + padding)
            .attr("width", function() {
                if (hasParams) return width * (7/9);
                else return width * (2/3);
            })
            // The height of the rectangle depends on the first and last
            // qubits on which the gate lays on (if gate=[0,2], the
            // rectangle will overlap the qubits 0, 1 and 2) 
            .attr("height", length * height - 2 * padding)
            .attr("fill", "white")
            .attr("rx", width/70)
            .attr("stroke", color)
            .attr("stroke-width", width/70);

    // Appending a dagger symbol on the top right corner of the
    // rectangle if a dagger is applied on the gate. The dagger is
    // arbitrarly designed. You don't want to touch it.
    if (gateData.dag == true) {
        // A vertical rectangle for the handle and the blade
        gateContainer.append("rect")
                .attr("x", function() {
                    if (hasParams) return width * (100/128);
                    else return width * (89/128);
                })
                .attr("y", height * gate.min() + width * (13/128))
                .attr("width", width * (5/128))
                .attr("height", width * (27/128))
                .attr("fill", color);
        // A horizontal one for the guard
        gateContainer.append("rect")
                .attr("x", function() {
                    if (hasParams) return width * (97/128);
                    else return width * (86/128);
                })
                .attr("y", height * gate.min() + width * (17/128))
                .attr("width", width * (11/128))
                .attr("height", width * (3/128))
                .attr("fill", color);
        // A triangle to sharpen the blade
        let x;
        let y;
        if (hasParams) {
            x = [width*(100/128), width*(105/128), width*(106/128)];
        } else {
            x = [width*(89/128), width*(94/128), width*(96/128)];
        }
        y = [width*(35/128), width*(23/128), width*(35/128)];
        for (let k = 0; k < 3; k++) {
            y[k] += height * gate.min() + width * (6/128);
        }
        gateContainer.append("polygon")
                .attr("points", x[0]+","+y[0]+" "+x[1]+","+y[1]+" "+
                        x[2]+","+y[2])
                .attr("fill", "white");
    }

    // Appending the name of the gate, in the rectangle, a bit over
    // its parameters if it has any
    gateContainer.append("text")
            .classed("gate-name", true)
            .attr("x", width/2)
            // Positionning the y origin on the first qubit of the
            // gate
            .attr("y", gate.min() * height)
            // Adjusting the y coordinate of the text at the middle
            // of the rectangle, a bit over its parameters, only if it
            // has any
            .attr("dy", function() {
                if (hasParams) return length * height/2;
                else return height * (length/2 + (1/7));
            })
            .attr("text-anchor", "middle")
            .attr("fill", color)
            // Adapting the font size to the length of the gate name
            .attr("font-size", function() {
                // If the gate name includes 4 or 5 characters, you 
                // adapt the font size to the length
                if ([4, 5].includes(gateData.gate.length)) {
                    const decrease = gateData.gate.length * .6;
                    return height/decrease;
                } else
                if (gateData.gate.length > 5) return height/2.5;
                else return height/2
            })
            // Display the name of the gate, with its end truncated
            // and replaced with ellipsis if it really is too long
            .text(function() {
                let display = "";
                if (gateData.gate.length <= 5) {
                    display += gateData.gate;
                } else {
                    for (let k = 0; k < 3; k++) {
                        display += gateData.gate[k];
                    } display += "...";
                }
                return display;
            });

    // Appending the parameters of the gate, in brackets, a bit
    // under the name of the gate
    if (hasParams) {
        gateContainer.append("text")
                .attr("x", width * .5)
                // Positionning the y origin on the first qubit of the
                // gate
                .attr("y", gate.min() * height)
                // Adjusting the y coordinate of the text at the middle
                // of the rectangle, a bit under the name of the gate
                // (the +.6 is to put the text under the name of the
                // the gate)
                .attr("dy", (length + .6) * height/2)
                .attr("text-anchor", "middle")
                .attr("fill", color)
                .attr("font-size", height * 2/7)
                // Display of the parameters in brackets (cf. the
                // function params_format())
                .text("(" + params_format(gateData.params) + ")");
    }
}

/**
 * Function to be called for each svg.slice element selected through D3;
 * it appends to each operator a line for each qubit the circuit
 * includes, along with its gate, whose representation depends on
 * its name, and its number, right above the gate.
 *
 * @param {object} svgSlice - The current svg slice
 * @param {object} gateData - The current gate needed data
 * @param {number} index - The gate index
 */
function draw_gate(svgSlice, gateData, index) {

    // This g tag will contain every graphic elements of a gate, and
    // will be the one on which you trigger the mouseenter and
    // mouseleave events
    const gateContainer = d3.select(svgSlice)
            .append("g")
            .classed("gate-container", true)
            .attr("id", "gate-" + index)
            .attr("transform", "translate(0, " + padding + ")");

    // Construction of the operator gate, function of its name, with
    // its extra control qubits if it has any
    if (gateData.gate === "CNOT" || gateData.gate === "CCNOT") {
        draw_cnot(gateContainer, gateData);
    } else
    if (gateData.gate === "CSIGN") {
        draw_csign(gateContainer, gateData);
        if (gateData.ctrl > 0) ctrl_qbits(gateContainer, gateData);
    } else
    if (gateData.gate === "SWAP") {
        draw_swap(gateContainer, gateData);
        if (gateData.ctrl > 0) ctrl_qbits(gateContainer, gateData);
    } else
    if (gateData.gate === "-REMAP-") {
        draw_remap(gateContainer, gateData);
    } else
    if (gateData.gate === "NO_OP") {
        // Nothing happens here; we just want the qubits to be displayed
        // since the circuit has no operator
    } else {
        // Here, ctrl_qbit() is called before draw_rect_gate(), and not
        // after, because of how it's been the most conveniently written
        if (gateData.ctrl > 0) ctrl_qbits(gateContainer, gateData);
        draw_rect_gate(gateContainer, gateData);
    }
}


/* ================================================================== */
/*      CONSTRUCTION OF THE CIRCUIT SKELETON                          */
/* ================================================================== */


/**
 * Initializes the display by building the table with a single row that
 * will wrap the entire circuit.
 */
function init_display() {

    // Initializing the display id (for convenient DOM manipulation)
    const index =
            d3.select("#circuit").node().parentNode.id.substring(8);

    // Setting the dimensions of the table that will content the circuit
    // display, both depending on the `width` variable, and its id
    const tabWidth = width * opsList.length;
    const tabHeight = height * nbQbits;
    table = d3.select("#circuit")
            .attr("id", "circuit-" + index)
            .style("width", ((tabWidth > 950) ? 950 : tabWidth) + "px")
            .style("height", tabHeight + "px")
            .style("padding", "0");

    // Adding the table row that will wrap the table columns
    display = table.append("tr")
            .attr("id", "display-" + index)
            .style("background-color", "white")
            .style("overflow-x", "scroll");

    // Implementing the qubits index below

    // Ancestor div element
    const ancestor = d3.select(table.node().closest(".output_wrapper"));

    // To check if the cell is already scrolled when the webpage is
    // displayed
    // TO FIX, THIS DOESN'T WORK
    const isScrolled = ancestor.select(".output")
            .attr("class").includes("output_scroll");

    // Column on the left on which the number of every qubit will be
    // displayed
    display.append("th")
                .style("right", "91%")
                .style("position", "absolute")
                .style("padding", "0")
            .append("svg")
                .attr("isHidden", function() {
                    if (isScrolled) return "true";
                    else return "false";
                })
                .attr("id", "qbits-list-" + index)
                .attr("width", "60px")
                .attr("height", tabHeight + "px");

    // Adding the name of every qubits on it, in the form of `qn` where
    // `n` is the qubit number
    const qbitsList = d3.select("#qbits-list-" + index);
    for (let k = 0; k < nbQbits; k++) {
        qbitsList.append("text")
                .attr("x", "50")
                .attr("y", (2 * k + 1) / 2 * height)
                .attr("dy", height/6)
                .attr("fill", function() {
                    if (isScrolled) return "none";
                    else return "black";
                })
                .attr("font-weight", "1")
                .attr("font-style", "italic")
                .attr("font-size", 13)
                .attr("text-anchor", "end")
                .text("q" + k);
    }

    // Here you'll add an onclick event on the "click to scroll output;
    // double-click to hide" div element of the cell, so that the qubits
    // list disappear when the user actually clicks on the div element
    ancestor.select(".prompt")
            .on("click", function() {
                const isHidden = qbitsList.attr("isHidden") === "true";
                if (isHidden) {
                    qbitsList.selectAll("text").attr("fill", "black");
                    qbitsList.attr("isHidden", "false");
                } else {
                    qbitsList.selectAll("text").attr("fill", "none");
                    qbitsList.attr("isHidden", "true");
                }
            });
}

/**
 * Generates a chunk of 50 operators of the circuit by generating 50
 * td tags with their svg tag within, then calling the draw_gate()
 * function to build the gates as they should be
 * 
 * @param {Array} chunk - The list of 50 operators with their attributes
 * @param {number} index - The current chunk index
 * @param {number} extended - 1 if the display must be extended, 0 if
 *     it must be compressed (which is the default value)
 */
function generate_chunk_slices(chunk, index, extended) {

    const slices = display.selectAll(".chunk-" + index)
            .data(chunk)
            .enter()
            .append("td")
                .attr("id", (d, i) => "slice-" + (index * 50 + i))
                .style("width", width + "px")
                .style("height", table.style("height"))
                .style("padding", 0)
            .append("svg")
                .classed("slice", true)
                .classed("chunk-" + index, true)
                .attr("width", width)
                .attr("height", parseFloat(table.style("height")) +
                        2 * padding + "px");

    // Construction of the lines embodying each qubit
    for (let k = 0; k < nbQbits; k++) {
        slices.append("line")
                .classed("qbit" + k, true)
                .attr("x1", 0)
                .attr("x2", width)
                .attr("y1", ((2 * k + 1) * height) / 2 + padding)
                .attr("y2", ((2 * k + 1) * height) / 2 + padding)
                .attr("stroke", color)
                .attr("stroke-width", width/70);
    }

    // Different treatment if the circuit must be displayed extended,
    // or compressed for visual convenience – as `d` will be different
    // for each case
    if (extended) {
        // Implementing every gates
        slices.each(function(d, i) {
            draw_gate(this, d, index * 50 + i);
        });
    } else {
        // Implementing every gates of each slice
        slices.each(function(d) {
            // Loop for each gate
            for (let k = 0; k < d.length; k++) {
                draw_gate(this, d[k], d[k].index);
            }
        });
    }
}


/* ================================================================== */
/*      ANIMATIONS MANAGEMENT                                         */
/* ================================================================== */


/**
 * Increases the size of some elements of the gate on which the
 * mouseenter event is triggered. These elements are:
 *  - the rectangle and name of standard gates
 *  - the dots of control qubits
 *  - the components of targets
 *  - the crosses of SWAP gates
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 * @param {number} width - The dimensions variable, the width of a slice
 */
function increase_size(gateContainer, gateData, width) {

    const height = width * (2/3);
    const padding = height/12;
    
    const treatment = qbits_list_treatment(gateData);
    const gate = treatment[0];
    const length = treatment[1];

    // Increase of the size of the rectangle embodying the gate
    d3.select(gateContainer)
            .select(".gate")
            .transition()
            .duration(500)
            // Moving the origin of the rectangle on the left
            .attr("x", function() {
                if (gateData.params.length > 0) {
                    return width/9 - padding * (2/3);
                } else {
                    return width/6 - padding;
                }
            })
            // Moving up the origin of the rectangle
            .attr("y", gate.min() * height + padding/3)
            // Increasing the width of the rectangle
            .attr("width", function() {
                if (gateData.params.length > 0) {
                    return width * (7/9) + padding * (4/3);
                } else {
                    return width * (2/3) + 2 * padding;
                }
            })
            // Increasing the height of the rectangle
            .attr("height", length * height - padding * (2/3));

    // Increase of the size of the gate name, if it has one
    const gateName = d3.select(gateContainer).select(".gate-name");
    if (gateName.node() != null) {
        const fontSize = parseFloat(gateName.attr("font-size"));
        const deltaY = parseFloat(gateName.attr("dy"));
        const hasParams = gateData.params.length > 0;
        gateName.transition()
                .duration(500)
                .attr("font-size", fontSize * 1.1)
                .attr("dy", function() {
                    if (hasParams) return deltaY;
                    else return deltaY + (fontSize * 0.05);
                });
    }

    // Increase of the radius of the control qubits dots
    d3.select(gateContainer)
            .selectAll(".dot")
            .transition()
            .duration(500)
            .attr("r", width * (1/10));

    // Increase of the radius of the target
    d3.select(gateContainer)
            .select(".target-circle")
            .transition()
            .duration(500)
            .attr("r", width * (11/36));

    // Increase of the length of the target vertical line
    const targeted = gate[0];
    d3.select(gateContainer)
            .select(".target-line")
            .transition()
            .duration(500)
            .attr("y1", height * (2 * targeted + 1)/2 - width * 11/36)
            .attr("y2", height * (2 * targeted + 1)/2 + width * 11/36);

    // Increase of the size of the crosses of a SWAP gate
    for (let k = 0; k < 2; k++) {
        d3.select(gateContainer)
                .select(".cross-0-"+k)
                .transition()
                .duration(500)
                .attr("x1", width * 8/24)
                .attr("x2", width * 16/24)
                .attr("y1", height * (2 * gate[k] + 1) / 2 - 
                        width * (4/24))
                .attr("y2", height * (2 * gate[k] + 1) / 2 +
                        width * (4/24));
        d3.select(gateContainer)
                .select(".cross-1-"+k)
                .transition()
                .duration(500)
                .attr("x1", width * 8/24)
                .attr("x2", width * 16/24)
                .attr("y1", height * (2 * gate[k] + 1) / 2 + 
                        width * (4/24))
                .attr("y2", height * (2 * gate[k] + 1) / 2 -
                        width * (4/24));
    }
}

/**
 * Gets the elements of the gate whose size has been increased back to
 * their original size.
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 * @param {number} width - The dimensions variable, the width of a slice
 */
function decrease_size(gateContainer, gateData, width) {

    const height = width * (2/3);
    const padding = height/12;
    
    const treatment = qbits_list_treatment(gateData);
    const gate = treatment[0];
    const length = treatment[1];

    // Getting the rectangle embodying the gate back to normal
    d3.select(gateContainer)
            .select(".gate")
            .transition()
            .duration(500)
            .attr("x", function() {
                if (gateData.params.length > 0) return width/9;
                else return width/6;
            })
            .attr("y", gate.min() * height + padding)
            .attr("width", function() {
                if (gateData.params.length > 0) return width * (7/9);
                else return width * (2/3);
            })
            .attr("height", length * height - 2 * padding);

    // Getting the gate name back to normal
    const gateName = d3.select(gateContainer).select(".gate-name")
    if (gateName.node() != null) {
        const deltaY = parseFloat(gateName.attr("dy"));
        const hasParams = gateData.params.length > 0;
        gateName.transition()
                .duration(500)
                .attr("dy", function() {
                    if (hasParams) return deltaY;
                    else return height * (length/2 + (1/7));
                })
                .attr("font-size", function() {
                    if ([4, 5].includes(gateData.gate.length)) {
                        const decrease = gateData.gate.length * .6;
                        return height/decrease;
                    } else
                    if (gateData.gate.length > 5) return height/2.5;
                    else return height/2;
                });
    }

    // Getting the dots of the control qubits back to normal
    d3.select(gateContainer)
            .selectAll(".dot")
            .transition()
            .duration(500)
            .attr("r", width/12);

    // Getting the circle of the target back to normal
    d3.select(gateContainer)
            .select(".target-circle")
            .transition()
            .duration(500)
            .attr("r", width/4);

    // Getting the vertical line of the target back to normal
    const targeted = gate[0];
    d3.select(gateContainer)
            .select(".target-line")
            .transition()
            .duration(500)
            .attr("y1", height * (2 * targeted + 1) / 2 - width/4)
            .attr("y2", height * (2 * targeted + 1) / 2 + width/4);

    // Getting the crosses of a SWAP gate back to normal
    for (let k = 0; k < 2; k++) {
        d3.select(gateContainer)
                .select(".cross-0-"+k)
                .transition()
                .duration(500)
                .attr("x1", width * 3/8)
                .attr("x2", width * 5/8)
                .attr("y1", height * (2 * gate[k] + 1) / 2 - width/8)
                .attr("y2", height * (2 * gate[k] + 1) / 2 + width/8);
        d3.select(gateContainer)
                .select(".cross-1-"+k)
                .transition()
                .duration(500)
                .attr("x1", width * 3/8)
                .attr("x2", width * 5/8)
                .attr("y1", height * (2 * gate[k] + 1) / 2 + width/8)
                .attr("y2", height * (2 * gate[k] + 1) / 2 - width/8);
    }
}

/**
 * Appends an svg tag on the display, set with the `position: absolute`
 * CSS property and the right `left` CSS proprty (taking the current
 * scrolling into account), so it is added over the displayed circuit,
 * at the right x position. Its id also depends on which function is
 * calling add_display().
 * Returns the actual svg tag.
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {string} origin - A string to identify which function has
 *     called add_display
 * @param {number} width - The dimensions variable, the width of a slice
 *
 * @return {object} dataContainer The created svg node
 */
function add_display(gateContainer, origin, width) {

    const height = width * (2/3);
    
    // Getting the number of the current operator, so to be able to
    // append the svg tag on the right x position
    const nth = parseInt(d3.select(gateContainer)
            .node()         // Getting the actual g node
            .parentNode     // Reaching the parent svg node
            .parentNode.id  // Getting the id of the parent td node
            .substring(6)); // Removing `slice-` to only keep the number

    // Building the svg tag on which you'll draw the data visualization
    const dataContainer = d3.select(gateContainer.parentNode.parentNode)
            .append("svg")
            .attr("id", function() {
                if (origin === "specs") return "specs";
                else if (origin === "matrix") return "matrix_svg";
            })
            .style("position", "absolute")
            .style("left", 115 + width * (nth + 1) -
                    gateContainer.closest(".output_html").scrollLeft
            )
            .attr("width", 700)
            .attr("height", function() {
                const parentSvg = d3.select(gateContainer.parentNode);
                const svgHeight = parseFloat(parentSvg.attr("height"));
                return svgHeight * 1.5;
            });

    return dataContainer;
}

/**
 * Displays the specifications of the gate hovered by the mouse in a
 * box, next to the mouse. These specifications are:
 *  - the operator number
 *  - the gate name
 *  - the list of qubits on which the gate is applied
 *  - its parameters, if it has any
 *  - whether a dagger is applied on it or not
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 */
function display_specs(gateContainer, gateData, width) {

    // Defining the metric of every padding, and the font size of the
    // texts
    const metric = 25/6;
    const fontSize = 50/3;

    // y origin of the elements set at some point a bit above where
    // the mouse passes over the gate, except on the extreme top of the
    // display (where there's no adjustment, so the box's not truncated)
    const mouseY = d3.mouse(gateContainer.parentNode.parentNode)[1];
    let yOrigin;
    if (mouseY < 4 * metric) yOrigin = mouseY;
    else if (mouseY < 8 * metric) yOrigin = mouseY - 4 * metric;
    else yOrigin = mouseY - 8 * metric;

    // Getting the svg element on which everything will be displayed
    const dataContainer = add_display(gateContainer, "specs", width);

    // Here you'll write the specifications of the gate on the new svg
    // tag, get their length, so to adapt the width of the rectangle
    // on which you want to display the specifications. Since the
    // rectangle is created after the texts, you append copies of them
    // on the rectangle so they're actually visible.

    // Declaration of the specifications box height
    let boxHeight = 12 * metric;

    // Displaying the number of the gate
    dataContainer.append("text")
            .attr("id", "number-display")
            .attr("x", metric * 2)
            .attr("y", yOrigin)
            .attr("dy", metric * 4)
            .attr("fill", "darkslategray")
            .attr("font-size", fontSize)
            .text("Gate #" + gateContainer.id.substring(5))
            .style("opacity", 0)
            .transition()
            .duration(500)
            .style("opacity", 1);
    // Getting the length of the text
    const numberLength = dataContainer.select("#number-display")
            .node().getBBox().width;

    // Displaying the name of the gate
    dataContainer.append("text")
            .attr("id", "name-display")
            .attr("x", metric * 2)
            .attr("y", yOrigin)
            .attr("dy", metric * 8)
            .attr("fill", "darkslategray")
            .attr("font-size", fontSize)
            .text("Name: " + gateData.gate)
            .style("opacity", 0)
            .transition()
            .duration(500)
            .style("opacity", 1);
    // Getting the length of the text
    const nameLength = dataContainer.select("#name-display")
            .node().getBBox().width;

    // Displaying the qubits on which the gate is applied
    dataContainer.append("text")
            .attr("id", "qbits-display")
            .attr("x", metric * 2)
            .attr("y", yOrigin)
            .attr("dy", metric * 12)
            .attr("fill", "darkslategray")
            .attr("font-size", fontSize)
            .text(function() {
                let display;
                if (gateData.qbits.length === 1) {
                    display = "Qubit: [" + gateData.qbits[0] + "]";
                } else {
                    display = "Qubits: [" + gateData.qbits[0];
                    for (let k = 1; k < gateData.qbits.length; k++) {
                        display = display + ", " + gateData.qbits[k];
                    } display += "]";
                }
                return display;
            })
            .style("opacity", 0)
            .transition()
            .duration(500)
            .style("opacity", 1);
    // Getting the length of the text
    const qbitsLength = dataContainer.select("#qbits-display")
            .node().getBBox().width;

    // This is for the next text y position
    let nextY = metric * 16;

    // Displaying the parameters of the gate, if it has any
    dataContainer.append("text")
            .attr("id", "params-display")
            .attr("x", metric * 2)
            .attr("y", yOrigin)
            .attr("dy", nextY)
            .attr("fill", "darkslategray")
            .attr("font-size", fontSize)
            .text(function() {
                let display;
                // This one condition is to make sure the text actually
                // vanishes when another data container is instantiated
                // (you can call it a debug condition)
                if (gateData.params.length === 0) {
                    display = "";
                } else
                // If the gate has parameters, displays them in square
                // brackets
                if (gateData.params.length === 1) {
                    display = "Parameter: [" + gateData.params[0] + "]";
                } else {
                    display = "Parameters: [" + gateData.params[0];
                    for (let k = 1; k < gateData.params.length; k++) {
                        display = display + ", " + gateData.params[k];
                    } display += "]";
                }
                return display;
            })
            .style("opacity", 0)
            .transition()
            .duration(500)
            .style("opacity", 1);
    // Adjusting the height of the specifications box if the gate
    // actually has parameters, and setting the next text y position
    if (gateData.params.length > 0) {
        boxHeight += 4 * metric;
        nextY += 4 * metric;
    }
    // Getting the length of the text
    const paramsLength = dataContainer.select("#params-display")
            .node().getBBox().width;

    // Reporting if a dagger is applied on the gate
    dataContainer.append("text")
            .attr("id", "dag-display")
            .attr("x", metric * 2)
            .attr("y", yOrigin)
            .attr("dy", nextY)
            .attr("fill", "darkslategray")
            .attr("font-size", fontSize)
            .text(function() {
                if (gateData.dag == false) return "";
                else return "Dagger applied";
            })
            .style("opacity", 0)
            .transition()
            .duration(500)
            .style("opacity", 1);
    // Adjusting the height of the specifications box if a dagger is
    // actually applied on the gate, and setting the next text y
    // position
    if (gateData.dag == true) {
        boxHeight += 4 * metric;
        nextY += 4 * metric;
    }
    // Getting the length of the text
    const dagLength = dataContainer.select("#dag-display")
            .node().getBBox().width;

    // Adjusting the length of the box according to the longer text it
    // wraps
    let boxWidth = nameLength;
    if (boxWidth < qbitsLength) boxWidth = qbitsLength;
    if (boxWidth < numberLength) boxWidth = numberLength;
    if (boxWidth < paramsLength) boxWidth = paramsLength;
    if (boxWidth < dagLength) boxWidth = dagLength;

    // Adding the actual box (a white and framed rectangle) on which the
    // specifications will be displayed
    dataContainer.append("rect")
            .attr("x", metric)
            .attr("y", yOrigin)
            .attr("width", boxWidth + 2 * metric)
            .attr("height", boxHeight + 1.5 * metric)
            .attr("stroke", color)
            .attr("stroke-width", 1)
            .attr("rx", 1)
            .attr("fill", "white")
            .style("opacity", 0)
            .transition()
            .duration(500)
            .style("opacity", 1);

    // Getting the texts back on the white rectangle (actually putting
    // copies of them on it)
    dataContainer.append("use").attr("xlink:href", "#number-display");
    dataContainer.append("use").attr("xlink:href", "#name-display");
    dataContainer.append("use").attr("xlink:href", "#qbits-display");
    dataContainer.append("use").attr("xlink:href", "#params-display");
    dataContainer.append("use").attr("xlink:href", "#dag-display");
}

/**
 * Makes the svg tag on which the specifications box is displayed vanish
 * and the text written on it disappear instantly so not to make it
 * flicker when another specifications box is displayed
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 */
function remove_specs(gateContainer) {

    d3.select(gateContainer.parentNode.parentNode)
            .selectAll("#specs")
            .transition()
            .duration(300)
            .style("opacity", 0)
            .remove();

    d3.select(gateContainer.parentNode.parentNode)
            .selectAll("#specs")
            .selectAll("text")
            .remove();
}

/**
 * Displays the gate matrix next to the mouse, by first removing the
 * display of the gate specifications, then adding a new svg tag, and
 * writing the matrix on it, with:
 *  - an opening round bracket (svg path)
 *  - every element of the matrix, at the right position (svg texts)
 *  - a closing round bracket (svg path)
 *  - a white rectangle beneath it so to shed a light on it (svg rect)
 *
 * If the `gateData` object has no attribute `matrix` (which may
 * happen), logs an explicit error in the console.
 *
 * If the gate is controlled, as control qubits modify poorly the matrix
 * of the original gate, indicates that the matrix is modified by n
 * control qubits with the following notation:
 *     ctrlⁿ[the_matrix]
 *
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 * @param {object} gateData - The current gate needed data
 */
function display_matrix(gateContainer, gateData, width) {

    // Defining the metric of every padding, and the font size of the
    // texts
    const metric = 25/6;
    const fontSize = 50/3;

    // Logging an explicit error in the console if the current
    // `gateData` object has no `matrix` attribute (which may happen)
    if (gateData.matrix === undefined) {
        throw new Error(gateContainer.id + 
                " has no `matrix` attribute");
    }

    // If the matrix is too wide (number of rows and columns exceeding
    // four), the matrix is not displayed, with an explicit error log in
    // the console
    else if (gateData.matrix.length > 4) {
        throw new Error(gateContainer.id +
                " matrix is too wide to be displayed");
    }

    // Displaying the matrix if the current `gateData` actually has one
    // that is not too wide
    else {

        remove_specs(gateContainer);

        // y origin of the elements set at some point a bit above where
        // the mouse passes over the gate, except on the extreme top of
        // the display (where there's no adjustment, so the box's not
        // truncated)
        const mouseY = d3.mouse(gateContainer.parentNode.parentNode)[1];
        let yOrigin;
        if (mouseY < 4 * metric) yOrigin = mouseY;
        else yOrigin = mouseY - 4 * metric;

        // Getting the svg element on which everything will be displayed
        const dataContainer = add_display(
            gateContainer, "matrix", width
        );

        const matrixHeight = gateData.matrix.length * 4 * metric;

        // Instantiation of the box (white rectangle) on which the
        // matrix will be displayed
        const box = dataContainer.append("rect")
                .attr("x", metric)
                .attr("y", yOrigin)
                .attr("height", matrixHeight + 2 * metric)
                .attr("rx", 10)
                .attr("fill", "white");

        // As control qubits modify poorly the matrix of the original
        // gate, here you simply explicitly indicate that the matrix is
        // modified by n control qubits with the notation:
        //     ctrlⁿ[the_matrix]
        dataContainer.append("text")
                    .attr("x", 2 * metric)
                    .attr("y", yOrigin)
                    .attr("dy", 2 * (gateData.matrix.length + 1) *
                            metric)
                    .attr("fill", "darkslategray")
                    .attr("font-size", fontSize)
                    .text(function() {
                        let display;
                        if (gateData.ctrl === 0) display = "";
                        else {
                            display = "ctrl";
                            if (gateData.ctrl <= 9) {
                                switch (gateData.ctrl) {
                                    case 1:
                                        display += "";
                                        break;
                                    case 2:
                                        display += "²";
                                        break;
                                    case 3:
                                        display += "³";
                                        break;
                                    case 4:
                                        display += "⁴";
                                        break;
                                    case 5:
                                        display += "⁵";
                                        break;
                                    case 6:
                                        display += "⁶";
                                        break;
                                    case 7:
                                        display += "⁷";
                                        break;
                                    case 8:
                                        display += "⁸";
                                        break;
                                    case 9:
                                        display += "⁹";
                                }
                            } else {
                                display += "¹⁰⁺";
                            }
                        }
                        return display;
                    })
                    .style("font-style", "italic")
                    .style("opacity", 0)
                    .transition()
                    .duration(500)
                    .style("opacity", 1);

        // Abscissa of the next item; initializing it function of if it
        // is a controlled gate or not (as there would be the `ctrlⁿ`
        // notation or not)
        let nextX;
        if (gateData.ctrl === 0) nextX = 4 * metric;
        else if (gateData.ctrl === 1) nextX = 11 * metric;
        else nextX = 12 * metric;

        // Adding the matrix opening bracket
        dataContainer.append("path")
                .attr("d", function() {
                    const yEnd = yOrigin + matrixHeight;
                    return "M" + nextX + "," +
                            (yOrigin + metric) +
                            " C" + (nextX - 3 * metric) + "," +
                            (yOrigin + 3 * metric) +
                            " " + (nextX - 3 * metric) + "," +
                            (yEnd - metric) +
                            " " + nextX + "," +
                            (yEnd + metric);
                })
                .attr("stroke", "darkslategray")
                .attr("stroke-width", 1)
                .attr("fill", "none")
                .style("opacity", 0)
                .transition()
                .duration(500)
                .style("opacity", 1);

        // Adding each complex number of the matrix, by writing down the
        // widest number of each column so to align the others with it
        // when displaying them, for each column

        // Loop for each column of the matrix
        for (let col = 0; col < gateData.matrix[0].length; col++) {

            // Determining which of the elements of a column is the
            // widest, the one that takes the more room
            let widest = gateData.matrix[0][col].length;
            let widestRowIndex = 0;
            for (let row = 1; row < gateData.matrix.length; row++) {
                if (gateData.matrix[row][col].length > widest) {
                    widest = gateData.matrix[row][col].length;
                    widestRowIndex = row;
                }
            }

            // Writing the widest element of the column to get its width
            dataContainer.append("text")
                    .classed("column-" + col, true)
                    .attr("x", nextX)
                    .attr("y", yOrigin)
                    .attr("dy", (widestRowIndex+1) * 4 * metric)
                    .attr("fill", "darkslategray")
                    .attr("font-size", fontSize)
                    .text(gateData.matrix[widestRowIndex][col])
                    .style("opacity", 0)
                    .transition()
                    .duration(500)
                    .style("opacity", 1);
            // Actually getting its width
            const widestWidth = d3.select(".column-" + col)
                    .node().getBBox().width;

            // Adding the other elements of the column
            for (let row = 0; row < gateData.matrix.length; row++) {
                if (row != widestRowIndex) {
                    dataContainer.append("text")
                            .classed("column-" + col, true)
                            .attr("x", nextX + widestWidth / 2)
                            .attr("y", yOrigin)
                            .attr("dy", (row+1) * 4 * metric)
                            .attr("fill", "darkslategray")
                            .attr("text-anchor", "middle")
                            .attr("font-size", fontSize)
                            .text(gateData.matrix[row][col])
                            .style("opacity", 0)
                            .transition()
                            .duration(500)
                            .style("opacity", 1);
                }
            }

            // Setting the abscissa value for the next column
            nextX += widestWidth + 3 * metric;
        }

        // Adding the matrix closing bracket
        dataContainer.append("path")
                .attr("d", function() {
                    const yEnd = yOrigin + matrixHeight;
                    return "M" + (nextX - 3 * metric) + "," +
                            (yOrigin + metric) + " C" +
                            nextX + "," +
                            (yOrigin + 3 * metric) + " " +
                            nextX + "," +
                            (yEnd - metric) + " " +
                            (nextX - 3 * metric) + "," +
                            (yEnd + metric);
                })
                .attr("stroke", "darkslategray")
                .attr("stroke-width", 1)
                .attr("fill", "none")
                .style("opacity", 0)
                .transition()
                .duration(500)
                .style("opacity", 1);

        // Setting the width of the rectangle beneath the matrix
        // function of the matrix width
        box.attr("width", nextX);
    }
}

/**
 * Makes the svg tag on which the matrix box is displayed vanish
 * 
 * @param {object} gateContainer - The current g tag wrapping the gate
 *     visualization
 */
function remove_matrix(gateContainer) {
    d3.selectAll("#matrix_svg")
            .transition()
            .duration(300)
            .style("opacity", 0)
            .remove();
}

/**
 * Applies the animation functions to all the gates of the current
 * display, and set some style to texts.
 *
 * @param {number} width - The dimension variable to apply to the
 *     animation functions (as the slices width)
 */
function init_animations(width) {
    
    table.selectAll("text").style("pointer-events", "none");

    table.selectAll(".gate-container")
            .on("mouseenter", function(d) {
                // Getting the data of the gate
                let gateData;
                const gateIndex = parseInt(this.id.substring(5));
                for (let k = 0; k < d.length; k++) {
                    // If the circuit must be extended, d.length=1 and
                    // gateData = d[0]; otherwise, you'll have to get
                    // the right gateData for the right slice gate (with
                    // matching index)
                    if (d[k].index === gateIndex) {
                        gateData = d[k];
                        break;
                    }
                }
                // Function called on `mouseenter`
                increase_size(this, gateData, width);
                display_specs(this, gateData, width);
            })
            .on("mouseleave", function(d) {
                // Getting the data of the gate
                let gateData;
                const gateIndex = parseInt(this.id.substring(5));
                for (let k = 0; k < d.length; k++) {
                    // Same behavior as above
                    if (d[k].index === gateIndex) {
                        gateData = d[k];
                        break;
                    }
                }
                // Functions called on `mouseleave`
                decrease_size(this, gateData, width);
                remove_specs(this);
                if (document.getElementById("matrix_svg") != null) {
                    remove_matrix(this);
                }
            })
            .on("click", function(d) {
                // Getting the data of the gate
                let gateData;
                const gateIndex = parseInt(this.id.substring(5));
                for (let k = 0; k < d.length; k++) {
                    // Same behavior as above
                    if (d[k].index === gateIndex) {
                        gateData = d[k];
                        break;
                    }
                }
                // Functions called on `click`
                if (document.getElementById("matrix_svg") === null) {
                    display_matrix(this, gateData, width);
                } else {
                    remove_matrix(this);
                }
            });
}


/* ================================================================== */
/*      SVG FILE EXPORT MANAGEMENT                                    */
/* ================================================================== */


/**
 * Saves on the computer (thanks to the `FileSaver.js` library) the
 * circuit svg display in a file named `sample.svg`
 */
function svg_export() {
    const xmlSerializer = new XMLSerializer();
    const svgNode = xmlSerializer.serializeToString(svg.node());
    const svgBlob = new Blob([svgNode], {type: "image/svg+xml"});
    saveAs(svgBlob, "sample.svg");
}

/**
 * Generates the circuit svg drawing in the DOM
 * 
 * @param {number} nbQbits - The circuit number of qubits
 * @param {Array} chunk - The list of 50 operators with their attributes
 * @param {number} index - The current chunk index
 * @param {number} extended - 1 if the display must be extended, 0 if
 *     it must be compressed (which is the default value)
 */
function generate_svg_file_slices(nbQbits, chunk, index, extended) {

    // Building every slice of display as an svg tag on which you'll
    // draw the circuit slice gates
    const slices = svg.selectAll(".chunk-" + index)
            .data(chunk)
            .enter()
            .append("svg")
            .attr("id", (d, i) => "slice-" + (index * 50 + i))
            .classed("slice", true)
            .classed("chunk-" + index, true)
            .attr("x", (d, i) => i * width)
            .attr("width", width + "px")
            .attr("height", svgHeight + "px");

    // Construction of the lines embodying each qubit
    for (let k = 0; k < nbQbits; k++) {
        slices.append("line")
                .classed("qbit" + k, true)
                .attr("x1", 0)
                .attr("x2", width)
                .attr("y1", ((2 * k + 1) * height) / 2 + padding)
                .attr("y2", ((2 * k + 1) * height) / 2 + padding)
                .attr("stroke", color)
                .attr("stroke-width", width/70);
    }

    // Different treatment if the circuit must be displayed extended,
    // or compressed for visual convenience – as `d` will be different
    // for each case
    if (extended) {
        // Implementing every gates
        slices.each(function(d, i) {
            draw_gate(this, d, index * 50 + i);
        });
    } else {
        // Implementing every gates of each slice
        slices.each(function(d) {
            // Loop for each gate
            for (let k = 0; k < d.length; k++) {
                draw_gate(this, d[k], d[k].index);
            }
        });
    }
}

/**
 * Calls the generate_svg_file_slices() function as many times as
 * necessary (i.e. for each chunk of 50 circuit slices)
 *
 * @param {array} slicesList - The list of every circuit slices
 * @param {number} extended - 1 if the display must be extended, 0 if
 *     it must be compressed (which is the default value)
 */
function generate_full_svg(slicesList, extended) {

    // Getting the number of chunks of 50 operators
    const chunksNb = Math.ceil(slicesList.length / 50);

    // Generating the chunks of display
    for (let k = 0; k < chunksNb; k++) {
        const chunk = slicesList.slice(0, 50);
        generate_svg_file_slices(nbQbits, chunk, k, extended);
    }
}

/**
 * Initializes the SVG export button
 *
 * @param {object} data - The circuit data
 * @param {number} theWidth - The width variable of the current circuit
 * @param {number} extended - 1 if the display must be extended, 0 if
 *     it must be compressed (which is the default value)
 */
function init_svg_print(data, theWidth, extended) {

    // Initializing the circuit number of qubits variable and the list
    // of circuit slices variable
    const nbQbits = data.nbqbits;
    const slicesList = [];
    
    // Buidling `slicesList`
    const dataCopy = JSON.parse(JSON.stringify(data));
    delete dataCopy["nbqbits"];
    for (let key in dataCopy) {
        slicesList.push(dataCopy[key]);
    }

    // Selecting the SVG-export wrapping div tag and customizing its id
    const svgWrapper = d3.select("#svg_wrapper")
            .attr("id", function() {
                return "svg_wrapper_" + this.parentNode.id.substring(8);
            });

    // Configuring the button
    const svgButton = d3.select("#svg_button")
            .attr("id", function() {
                return "svg_button_" + this.parentNode.id.substring(8);
            })
            .style("left", "200px")
            .style("color", "white")
            .style("background-color", "darkgray")
            .style("width", "100px")
            .style("height", "25px")
            .style("border-radius", "10px")
            .style("border", "none")
            .style("outline", "none")
            .on("click", function() {

                // When the button will be clicked, the dimension
                // variables of the associated circuit will be set as
                // global variables, so not to be polluted by the ones
                // of other circuits in the notebook
                width = theWidth;
                height = width * (2/3);
                padding = height/12;
                svgHeight = nbQbits * height;
                svgWidth = width * opsList.length;

                // Setting the wrapping svg tag (the drawing canvas)
                svg = svgWrapper.append("svg")
                        .attr("xmlns", "http://www.w3.org/2000/svg")
                        .attr("id", "svg2export")
                        .attr("height", svgHeight + 2 * padding)
                        .attr("width", svgWidth);

                // Drawing the circuit
                generate_full_svg(slicesList, extended);
                // Exporting it in a `.svg` file
                svg_export();
                // Removing the drawing so the user doesn't actually
                // see it
                svg.remove();
            });
}

var url_lookup = {
    "wP": "https://upload.wikimedia.org/wikipedia/commons/0/04/Chess_plt60.png",
    "wN": "https://upload.wikimedia.org/wikipedia/commons/2/28/Chess_nlt60.png",
    "wB": "https://upload.wikimedia.org/wikipedia/commons/9/9b/Chess_blt60.png",
    "wR": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Chess_rlt60.png",
    "wQ": "https://upload.wikimedia.org/wikipedia/commons/4/49/Chess_qlt60.png",
    "wK": "https://upload.wikimedia.org/wikipedia/commons/3/3b/Chess_klt60.png",

    "bP": "https://upload.wikimedia.org/wikipedia/commons/c/cd/Chess_pdt60.png",
    "bN": "https://upload.wikimedia.org/wikipedia/commons/f/f1/Chess_ndt60.png",
    "bB": "https://upload.wikimedia.org/wikipedia/commons/8/81/Chess_bdt60.png",
    "bR": "https://upload.wikimedia.org/wikipedia/commons/a/a0/Chess_rdt60.png",
    "bQ": "https://upload.wikimedia.org/wikipedia/commons/a/af/Chess_qdt60.png",
    "bK": "https://upload.wikimedia.org/wikipedia/commons/e/e3/Chess_kdt60.png",
}

function pieceTheme(piece) {
    return url_lookup[piece]
}


/***************************************************************************************
*    Copied code section
*    Title: Only Allow Legal Moves (Sample)
*    Author: Chris Oakman
*    Date: 9/27/2019
*    Code version: N/A
*    Availability: https://chessboardjs.com/examples#5003
*
***************************************************************************************/

var board = null
var game = new Chess()
var $status = $('#status')
var $fen = $('#fen')
var $pgn = $('#pgn')

function onDragStart(source, piece, position, orientation) {
    // do not pick up pieces if the game is over
    if (game.game_over()) return false

    console.log(source, piece, position, orientation);

    // only pick up pieces for the side to move
    if ((game.turn() === 'w' && piece.search(/^b/) !== -1) ||
        (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
        return false;
    }

    // only pick up pieces that can move
    if (game.moves({square: source}).length == 0){
        return false;
    }
}

function onDrop(source, target) {
    // see if the move is legal
    var move = game.move({
        from: source,
        to: target,
        promotion: 'q' // NOTE: always promote to a queen for example simplicity
    })

    // illegal move
    if (move === null) return 'snapback'

    // updateStatus()
}

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd() {
    board.position(game.fen())
}

// function updateStatus() {
//     var status = ''

//     var moveColor = 'White'
//     if (game.turn() === 'b') {
//         moveColor = 'Black'
//     }

//     // checkmate?
//     if (game.in_checkmate()) {
//         status = 'Game over, ' + moveColor + ' is in checkmate.'
//     }

//     // draw?
//     else if (game.in_draw()) {
//         status = 'Game over, drawn position'
//     }

//     // game still on
//     else {
//         status = moveColor + ' to move'

//         // check?
//         if (game.in_check()) {
//             status += ', ' + moveColor + ' is in check'
//         }
//     }

//     $status.html(status)
//     $fen.html(game.fen())
//     $pgn.html(game.pgn())
// }

function onMouseoverSquare(square, piece) {
    // get list of possible moves for this square
    var moves = game.moves({
        square: square,
        verbose: true
    })

    // exit if there are no moves available for this square
    if (moves.length === 0) return

    // highlight the square they moused over
    greySquare(square)

    // highlight the possible squares for this piece
    for (var i = 0; i < moves.length; i++) {
        greySquare(moves[i].to)
    }
}

function onMouseoutSquare(square, piece) {
    removeGreySquares()
}

var whiteSquareGrey = '#a9a9a9'
var blackSquareGrey = '#696969'

function removeGreySquares() {
    $('#myBoard .square-55d63').css('background', '')
}

function greySquare(square) {
    var $square = $('#myBoard .square-' + square)

    var background;
    if ($square.hasClass('black-3c85d')) {
        background = blackSquareGrey
    } else {
        background = whiteSquareGrey
    }

    $square.css('background', background)
}

var config = {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    onMouseoutSquare: onMouseoutSquare,
    onMouseoverSquare: onMouseoverSquare,
    // pieceTheme: pieceTheme,
}

/***************************************************************************************
*    END OF COPIED CODE SECTION
*
***************************************************************************************/

window.onload = function () {
    board = Chessboard('myBoard', config)
}
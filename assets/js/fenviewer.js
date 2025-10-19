( function( $ ){

	$( ".pgn-game" ).each( function(){
		var $pgnDiv = $( this );

		$.get( $pgnDiv.data( "url" ), function( pgn ){
			var containerId = "_" + Math.round(new Date().getTime() + (Math.random() * 100));
			$pgnDiv.after( $( '<div class="pgn-viewer-game" id="' + containerId + '"></div>' ) );

			var board = PGNV.pgnView( containerId, {
				pgn: pgn,
				theme: 'brown',
				pieceStyle: 'wikipedia',
				showCoords: false,
				boardSize: '400px',
				width: '100%',
				layout: 'left'
			});
		} );
	} );

	$( ".fen-position" ).each( function(){
		var $pgnDiv     = $( this )
		  , fen         = $pgnDiv.text()
		  , containerId = "_" + Math.round(new Date().getTime() + (Math.random() * 100));

		$pgnDiv.before( $( '<div class="pgn-viewer-game pgn-viewer-position" id="' + containerId + '"></div>' ) );

		// Create FEN copy container with input and copy button
		var fenContainer = $('<div class="fen-copy-container"></div>');
		var fenInput = $('<input type="text" value="' + fen + '" class="fen-input" readonly />');
		var copyBtn = $('<a class="fen-copy-btn btn"><i class="fas fa-copy"></i> Copy FEN</a>');
		var lichessLink = $('<a class="btn" href="https://lichess.org/analysis/' + fen + '" target="_blank"><i class="fas fa-external-link-alt"></i> Lichess</a>');

		fenContainer.append(fenInput).append(copyBtn).append(lichessLink);
		$pgnDiv.after(fenContainer);
		$pgnDiv.remove();

		PGNV.pgnBoard( containerId, {
			position: fen,
			theme: 'green',
			pieceStyle: 'wikipedia',
			showCoords: true,
			coordsInner: false,
			boardSize: '300px',
			width: '100%',
			layout: 'top',
			resizable:false,
		});

	} );

	// Add copy functionality for FEN inputs
	$(document).on('click', '.fen-copy-btn', function() {
		var $btn = $(this);
		var $input = $btn.siblings('.fen-input');
		var fen = $input.val();

		// Try to copy to clipboard
		if (navigator.clipboard && window.isSecureContext) {
			navigator.clipboard.writeText(fen).then(function() {
				showCopyFeedback($btn);
			}).catch(function(err) {
				fallbackCopyTextToClipboard(fen, $btn);
			});
		} else {
			fallbackCopyTextToClipboard(fen, $btn);
		}
	});

	// Fallback copy method for older browsers
	function fallbackCopyTextToClipboard(text, $btn) {
		var textArea = document.createElement("textarea");
		textArea.value = text;
		textArea.style.top = "0";
		textArea.style.left = "0";
		textArea.style.position = "fixed";
		textArea.style.opacity = "0";

		document.body.appendChild(textArea);
		textArea.focus();
		textArea.select();

		try {
			var successful = document.execCommand('copy');
			if (successful) {
				showCopyFeedback($btn);
			} else {
				console.error('Fallback: Copying text command was unsuccessful');
			}
		} catch (err) {
			console.error('Fallback: Oops, unable to copy', err);
		}

		document.body.removeChild(textArea);
	}

	// Show visual feedback when copy is successful
	function showCopyFeedback($btn) {
		var originalHtml = $btn.html();
		$btn.addClass('copied').text('Copied!');

		setTimeout(function() {
			$btn.removeClass('copied').html(originalHtml);
		}, 2000);
	}

	$( ".datatable" ).DataTable();

} )( jQuery );
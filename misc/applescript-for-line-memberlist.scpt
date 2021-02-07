tell application "System Events" to tell process "LINE"
	set frontmost to true
	
	-- press down and get into the list
	key code 125
	
	-- press home
	key code 115
	delay 1
	
	-- page down
	repeat 5 times
		repeat 50 times
			--	press End
			key code 119
			--	delay 1
		end repeat
		delay 0.2
	end repeat
	
	-- back to home
	-- press Home
	key code 115
	
	
	
	local counter
	local max_index
	set counter to 1
	
	
	tell its UI element "聊天成員"
		tell its UI element 1
			-- walk all members
			
			-- get boundary
			try
				repeat with i from 1 to 30
					
					UI element i
					set max_index to i
				end repeat
				
			on error
				log "max_index: " & max_index
			end try
			
			-- get first page
			log "get first page"
			repeat with i from 1 to max_index
				set s to get the size of UI element i
				set p to get the position of UI element i
				
				
				
				set width to 250
				set x to 10 + (item 1 of p)
				set y to item 2 of p
				--				key code 125
				
				-- args: 
				-- -R<x,y,w,h> capture screen rect
				set args to "" & x & "," & y & "," & width & "," & item 2 of s
				
				do shell script "screencapture -x -R" & args & " ./data" & counter & ".png"
				set counter to counter + 1
			end repeat
			
			
			-- press home
			key code 115
			
			repeat with k from 1 to max_index
				key code 125
			end repeat
			
			repeat with member from 1 to 1530
				
				--			attributes
				-- 			size of properties
				set s to get the size of UI element (max_index - 1)
				set p to get the position of UI element (max_index - 1)
				
				
				
				set width to 250
				set x to 10 + (item 1 of p)
				set y to item 2 of p
				
				-- args: 
				-- -R<x,y,w,h> capture screen rect
				set args to "" & x & "," & y & "," & width & "," & item 2 of s
				
				do shell script "screencapture -x -R" & args & " ./data" & counter & ".png"
				set counter to counter + 1
				
				
				-- go next
				key code 125
				
			end repeat
			
			
			--	press End
			key code 119
			key code 119
			
			-- last page
			repeat with member from 2 to max_index
				
				set s to get the size of UI element member
				set p to get the position of UI element member
				
				set width to 250
				set x to 10 + (item 1 of p)
				set y to item 2 of p
				
				-- args: 
				-- -R<x,y,w,h> capture screen rect
				set args to "" & x & "," & y & "," & width & "," & item 2 of s
				
				do shell script "screencapture -x -R" & args & " ./data" & counter & ".png"
				set counter to counter + 1
				
			end repeat
			
			
			
		end tell
	end tell
end tell


local var_0_0 = ...
local var_0_1 = class("App")

function var_0_1.ctor(arg_1_0)
	print("App ctor")

	me.app = arg_1_0
	arg_1_0.__TraceDataOnAppPauseTime = 0
	arg_1_0.__TraceDataOnAppPauseTimeEx = 0
	arg_1_0.__TraceDataShowViewStamp__ = nil
end

function var_0_1.Start(arg_1_0)
	LuaHelper.RegisterLuaUpdate(handler(arg_1_0, arg_1_0.Update))
	LuaHelper.RegisterFunc(LuaEventDefine.APPLICATION_QUIT, handler(arg_1_0, arg_1_0.OnAppQuit))
	LuaHelper.RegisterFunc(LuaEventDefine.APPLICATION_PAUSE, handler(arg_1_0, arg_1_0.OnAppPause))
	LuaHelper.RegisterFunc(LuaEventDefine.APPLICATION_FOCUS, handler(arg_1_0, arg_1_0.OnAppFocus))
	LuaHelper.RegisterFunc(LuaEventDefine.ESCAPE, handler(arg_1_0, arg_1_0.OnEscape))
	LuaHelper.RegisterFunc(LuaEventDefine.LUA_STOP, handler(arg_1_0, arg_1_0.Stop))
	LuaHelper.RegisterFunc(LuaEventDefine.LOW_MEMORY, handler(arg_1_0, arg_1_0.OnLowMemory))
	LuaHelper.RegisterFunc(LuaEventDefine.SOUND_EVENT_CALLBACK, handler(arg_1_0, arg_1_0.OnSoundEventCallback))
	LuaHelper.RegisterFunc(LuaEventDefine.SCREEN_RESOLUTION_CHANGE, handler(arg_1_0, arg_1_0.OnScreenResolutionChange))

	if GlobalDefine.IsY25_M6CSharpCode then
		LuaHelper.RegisterFunc(LuaEventDefine.SCREEN_REAL_RESOLUTION_CHANGE, handler(arg_1_0, arg_1_0.OnRealScreenResolutionChange))
	end

	LuaHelper.RegisterFunc(LuaEventDefine.NOTIFICATION_AUTHORIZATION_RECEVIVED, handler(arg_1_0, arg_1_0.AuthorizationReciverd))
	LuaHelper.RegisterFunc(LuaEventDefine.GET_LANGUAGE_TEXT, function(arg_2_0, arg_2_1)
		return i18n(arg_2_0, arg_2_1)
	end)
	LuaHelper.RegisterFunc(LuaEventDefine.TOGGLE_CHEAT, handler(arg_1_0, arg_1_0.ToggleCheat))
	LuaHelper.RegisterButtonDisable(function(arg_2_0)
		GHelper.ViewHelper.OpenToast(i18n(arg_2_0))
	end)
	LuaHelper.BestHttpCleanCache(1296000, 52428800)

	if GlobalDefine.IsPetCSharpCode then
		LuaHelper.CheckVersionManifest()
	end

	printDR("APP->IsOldVersion:", me.IsOldVersion)
	printDR("APP->CSharpVersion:", me.csharpVersionCode)

	me.moduleManager = require("game.module.ModuleManager").new()
	arg_1_0._moduleManager = me.moduleManager

	arg_1_0._moduleManager:InitModules(function()
		arg_1_0._moduleManager:LateInitModules(function()
			arg_1_0._moduleManager:AddUpdateModules()
			GameMsg.SendMessage(GameMsgId.FRAMEWORK_READY)
			GHelper.SDKTraceDataHelper.TraceData_FirstOpen()
		end)
	end)
	GHelper.PostProcessDeviceLevelHelper.CheckRealTimeShadow()
end

function var_0_1.Stop(arg_1_0)
	printTT("App:Stop()")

	if arg_1_0._moduleManager then
		me.isShutdown = true

		arg_1_0._moduleManager:Dispose()

		arg_1_0._moduleManager = nil
		GModule = nil
		me.isShutdown = false
	end
end

function var_0_1.AuthorizationReciverd(arg_1_0, arg_1_1)
	return
end

function var_0_1.Quit(arg_1_0)
	printTT("App:Quit()")
	print("MoveTaskToBack")
	NativeHelper.MoveTaskToBack()
end

function var_0_1.OnAppQuit(arg_1_0)
	GameMsg.SendMessage(GameMsgId.FRAMEWORD_APP_QUIT, true)
	printTT("App:OnAppQuit()")
end

local var_0_2 = 0

function var_0_1.OnAppPause(arg_1_0, arg_1_1)
	local var_1_0

	if arg_1_1 then
		var_0_2 = TimeUtil.MiliTime()
		arg_1_0.__OnAppPauseStartTime = os.clock()

		print("App:OnAppPause", arg_1_1)
	else
		var_1_0 = TimeUtil.MiliTime() - var_0_2

		if arg_1_0.__OnAppPauseStartTime then
			arg_1_0.__TraceDataOnAppPauseTime = arg_1_0.__TraceDataOnAppPauseTime + os.clock() - arg_1_0.__OnAppPauseStartTime
			arg_1_0.__TraceDataOnAppPauseTimeEx = arg_1_0.__TraceDataOnAppPauseTimeEx + os.clock() - arg_1_0.__OnAppPauseStartTime
		end

		print("App:OnAppPause", arg_1_1)
	end

	GameMsg.SendMessage(GameMsgId.FRAMEWORD_APP_ONAPPPAUSE, arg_1_1, var_1_0)

	if not UserData.IsInGame() then
		return
	end

	GHelper.SDKTraceDataHelper.TraceData_OnAppPause(arg_1_1)
end

function var_0_1.OnAppFocus(arg_1_0, arg_1_1)
	printTT("App:OnAppFocus+", arg_1_1)
end

function var_0_1.OnEscape(arg_1_0)
	GameMsg.SendMessage(GameMsgId.FRAMEWORD_ANDROID_ESCAPE)
end

function var_0_1.OnLowMemory(arg_1_0)
	GameMsg.SendMessage(GameMsgId.FRAMEWORD_LOW_MEMORY)
end

function var_0_1.OnSoundEventCallback(arg_1_0, arg_1_1, arg_1_2)
	local var_1_0 = string.split(arg_1_1, "-")

	if #var_1_0 < 2 then
		return
	end

	if var_1_0[1] == "play" then
		GHelper.SoundHelper.Play(var_1_0[2])
	else
		GameMsg.SendMessage(GameMsgId.FRAMEWORD_SOUND_CALLBACK, arg_1_1, arg_1_2)
	end
end

function var_0_1.OnScreenResolutionChange(arg_1_0)
	me.RealScreenWidth = GameConfig.realWidth
	me.RealScreenHeight = GameConfig.realHeight

	print("-->OnScreenResolutionChange", me.RealScreenWidth, me.RealScreenHeight)
	GameMsg.SendMessage(GameMsgId.FRAMEWORK_SCREEN_RESOLUTION_CHANGED)
end

function var_0_1.OnRealScreenResolutionChange(arg_1_0)
	me.RealScreenWidth = GameConfig.realWidth
	me.RealScreenHeight = GameConfig.realHeight

	AppInitScreenSize()
	AppCheckUIFit()

	local var_1_0 = GModule.SceneModule:GetCurScene()

	if var_1_0 then
		if var_1_0._bIsApplySafeArea then
			ApplySafeArea()
		else
			UnApplySafeArea()
		end
	end

	printDR("App:OnRealScreenResolutionChange:", me.RealScreenHalfSize.x, me.RealScreenHalfSize.y)
	GModule.TimerModule:StartFrame(arg_1_0, function()
		GameMsg.SendMessage(GameMsgId.FRAMEWORK_SCREEN_RESOLUTION_CHANGED)
	end, 1, 1)
end

function var_0_1.Update(arg_1_0, arg_1_1, arg_1_2)
	if arg_1_0._moduleManager == nil then
		return
	end

	arg_1_0._moduleManager:Update(arg_1_1, arg_1_2)
	arg_1_0._moduleManager:FixedUpdate(arg_1_1)
end

function var_0_1.GetLangText(arg_1_0, arg_1_1)
	return i18n(arg_1_1)
end

function var_0_1.InitModuleFinish(arg_1_0)
	LuaHelper.GameReady()
end

function var_0_1.ToggleCheat(arg_1_0)
	if arg_1_0._isOpenCheat then
		arg_1_0._isOpenCheat = false

		GModule.UIModule:CloseView(GViewId.CHEAT_AIDE)
	else
		arg_1_0._isOpenCheat = true

		if GHelper.LoginHelper.GetIsShowCheat() then
			GModule.UIModule:OpenView(GViewId.CHEAT_AIDE)
		end
	end
end

return var_0_1

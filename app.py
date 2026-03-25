import React, { useState, useEffect, useRef } from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Plus, MapPin, Clock, X, ChevronDown, Edit3, Trash2, Copy, AlertCircle, CheckCircle2 } from 'lucide-react';

// iOS风格滚轮组件
const ScrollPicker = ({ items, value, onChange, label }) => {
  const containerRef = useRef(null);
  const ITEM_HEIGHT = 44; // 还原iOS标准触控高度

  // 初始滚动位置定位
  useEffect(() => {
    const index = items.findIndex(item => item.value === value);
    if (containerRef.current && index !== -1) {
      containerRef.current.scrollTop = index * ITEM_HEIGHT;
    }
  }, []); // 仅挂载时执行一次，后续交由用户滑动控制

  const handleScroll = (e) => {
    const scrollTop = e.target.scrollTop;
    const index = Math.round(scrollTop / ITEM_HEIGHT);
    if (items[index] && items[index].value !== value) {
      onChange(items[index].value);
    }
  };

  return (
    <div className="relative h-[220px] flex-1 flex justify-center items-center overflow-hidden picker-mask">
      {/* 中间高亮指示条 */}
      <div className="absolute top-[88px] left-2 right-2 h-[44px] bg-gray-100/60 rounded-xl pointer-events-none -z-10" />
      
      {/* 滚动容器 */}
      <div 
        ref={containerRef}
        onScroll={handleScroll}
        className="h-full w-full overflow-y-auto snap-y snap-mandatory hide-scrollbar z-10"
        style={{ paddingBottom: '88px', paddingTop: '88px' }}
      >
        {items.map((item) => (
          <div 
            key={item.value} 
            className={`h-[44px] flex items-center justify-center snap-center transition-all duration-200 cursor-grab active:cursor-grabbing
              ${item.value === value ? 'text-gray-900 font-bold text-[17px]' : 'text-gray-400 text-sm scale-95'}`}
          >
            {item.label} <span className="text-xs ml-1 opacity-60 font-normal">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const PhotographerCalendarApp = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());

  // 2. 数据持久化：读取本地存储 (Local Storage)
  const [events, setEvents] = useState(() => {
    const saved = localStorage.getItem('photographer_events');
    if (saved) {
      return JSON.parse(saved).map(e => ({...e, date: new Date(e.date)}));
    }
    // 没有本地数据时的初始默认数据
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    return [
      { id: 1, date: new Date(year, month, 2), title: '领证跟拍', type: 'registration', typeLabel: '领证', time: '全天' },
      { id: 9, date: new Date(year, month, 16), title: '婚礼跟拍', type: 'wedding', typeLabel: '婚礼', time: '08:00 - 18:00', location: '玫瑰庄园酒店', client: '张小姐', phone: '138-xxxx-xxxx', remarks: '需要提前半小时到场准备，新娘要求多拍些伴娘互动。' },
    ];
  });

  // 监听 events 变化并保存到本地
  useEffect(() => {
    localStorage.setItem('photographer_events', JSON.stringify(events));
  }, [events]);

  // 控制每日订单弹窗的状态
  const [showDayModal, setShowDayModal] = useState(false);
  
  // iOS风格年月选择器相关状态
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [pickerYear, setPickerYear] = useState(new Date().getFullYear());
  const [pickerMonth, setPickerMonth] = useState(new Date().getMonth());

  // 生成前后10年的选项
  const years = Array.from({ length: 21 }, (_, i) => new Date().getFullYear() - 10 + i).map(y => ({ label: y, value: y }));
  const months = Array.from({ length: 12 }, (_, i) => ({ label: i + 1, value: i }));

  const handleConfirmDate = () => {
    const newDate = new Date(pickerYear, pickerMonth, 1);
    setCurrentDate(newDate);
    setSelectedDate(newDate);
    setShowDatePicker(false);
  };

  // 生成 30 分钟间隔的时间数组 (00:00 到 23:30)
  const timeOptions = Array.from({ length: 48 }, (_, i) => {
    const hour = Math.floor(i / 2).toString().padStart(2, '0');
    const minute = i % 2 === 0 ? '00' : '30';
    return `${hour}:${minute}`;
  });

  // 新建档期相关状态
  const [showAddModal, setShowAddModal] = useState(false);
  const [formData, setFormData] = useState({
    client: '',
    type: 'wedding',
    date: '',
    timeMode: 'fuzzy',     // 新增: 'fuzzy' 模糊 | 'exact' 精确
    fuzzyTime: '全天',      // 新增: 模糊时间默认值
    exactStart: '09:00',   // 新增: 精确开始时间默认值
    exactEnd: '12:00',     // 新增: 精确结束时间默认值
    location: '',
    remarks: ''
  });

  const [isAddingCustom, setIsAddingCustom] = useState(false);
  const [tempCustomType, setTempCustomType] = useState('');
  const [isEditingTypes, setIsEditingTypes] = useState(false); // 新增：是否处于管理(编辑)模式

  // 1. 编辑与删除：新增状态
  const [editingEventId, setEditingEventId] = useState(null);
  const [deletePendingId, setDeletePendingId] = useState(null); // 新增：等待删除确认的订单ID

  // 3. 冲突提醒：新增状态
  const [conflictPendingData, setConflictPendingData] = useState(null);

  // 4. 行程分享：Toast状态
  const [toastMsg, setToastMsg] = useState('');

  // 内置订单类型 (变更为动态状态，允许将自定义标签固定在选项中，并支持本地持久化)
  const [dynamicEventTypes, setDynamicEventTypes] = useState(() => {
    const saved = localStorage.getItem('photographer_types');
    if (saved) return JSON.parse(saved);
    return [
      { id: 'wedding', label: '婚礼' },
      { id: 'engagement', label: '订婚宴' },
      { id: 'birthday', label: '周岁宴' },
      { id: 'registration', label: '领证' },
      { id: 'creative', label: '创作' },
      { id: 'banquet', label: '答谢宴' }
    ];
  });

  // 监听类型变化并保存
  useEffect(() => {
    localStorage.setItem('photographer_types', JSON.stringify(dynamicEventTypes));
  }, [dynamicEventTypes]);

  const handleConfirmCustom = () => {
    const val = tempCustomType.trim();
    if (val) {
      const newId = 'custom_' + Date.now();
      const newType = { id: newId, label: val };
      // 避免重复添加
      setDynamicEventTypes(prev => {
        if (prev.find(t => t.label === val)) return prev;
        return [...prev, newType];
      });
      setFormData(prev => ({ ...prev, type: newId }));
    }
    setIsAddingCustom(false);
    setTempCustomType('');
  };

  // 新增：删除类型的核心逻辑
  const handleDeleteType = (e, id) => {
    e.stopPropagation(); // 阻止点击事件冒泡
    setDynamicEventTypes(prev => {
      const newTypes = prev.filter(t => t.id !== id);
      // 优化：如果删除的是当前正在选中的类型，自动切换到第一个可用类型
      if (formData.type === id) {
        setFormData(f => ({ ...f, type: newTypes.length > 0 ? newTypes[0].id : '' }));
      }
      return newTypes;
    });
  };

  // 3. 智能防错：冲突检测逻辑
  const getConflictWarning = (eventDate, timeMode, fuzzyTime, exactStart, exactEnd, excludeId) => {
    const sameDayEvents = events.filter(e => isSameDate(e.date, eventDate) && e.id !== excludeId);
    if (sameDayEvents.length === 0) return null;

    if (timeMode === 'fuzzy' && fuzzyTime === '全天') {
      return '您已在此日期安排了其他行程，添加“全天”会导致档期重叠。';
    }

    const getMins = (timeStr) => {
      const [h, m] = timeStr.split(':').map(Number);
      return h * 60 + m;
    };

    const newStartMins = timeMode === 'exact' ? getMins(exactStart) : null;
    const newEndMins = timeMode === 'exact' ? getMins(exactEnd) : null;

    for (let e of sameDayEvents) {
      if (e.time && e.time.includes('全天')) {
        return `该日期已有“全天”行程（${e.title}），会导致档期重叠。`;
      }
      if (timeMode === 'exact' && e.time && e.time.includes('-')) {
        const [eStart, eEnd] = e.time.split('-').map(s => s.trim());
        const eStartMins = getMins(eStart);
        const eEndMins = getMins(eEnd);
        if (newStartMins < eEndMins && newEndMins > eStartMins) {
          return `与已有行程（${e.title} ${e.time}）时间发生重叠！`;
        }
      }
    }
    return null;
  };

  const handleSaveEvent = () => {
    if (!formData.client || !formData.date) return;
    
    const [y, m, d] = formData.date.split('-');
    const eventDate = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
    
    const typeLabel = dynamicEventTypes.find(t => t.id === formData.type)?.label || '其他类型';

    // 组装最终存入的时间字符串
    const finalTime = formData.timeMode === 'fuzzy' ? formData.fuzzyTime : `${formData.exactStart} - ${formData.exactEnd}`;

    // 校验冲突
    const warningMsg = getConflictWarning(eventDate, formData.timeMode, formData.fuzzyTime, formData.exactStart, formData.exactEnd, editingEventId);
    
    const newEvent = {
      id: editingEventId || Date.now(),
      date: eventDate,
      title: `${formData.client} - ${typeLabel}`,
      type: formData.type,
      typeLabel: typeLabel, 
      time: finalTime,
      location: formData.location,
      client: formData.client,
      remarks: formData.remarks,
    };

    if (warningMsg) {
      setConflictPendingData({ newEvent, warningMsg });
      return;
    }

    executeSave(newEvent);
  };

  const executeSave = (eventObj) => {
    setEvents(prev => {
      if (editingEventId) {
        return prev.map(e => e.id === editingEventId ? eventObj : e);
      }
      return [...prev, eventObj];
    });
    
    setSelectedDate(eventObj.date);
    
    // 如果录入的日期不在当前月份，则自动跳转月份
    if (eventObj.date.getMonth() !== currentDate.getMonth() || eventObj.date.getFullYear() !== currentDate.getFullYear()) {
      setCurrentDate(new Date(eventObj.date.getFullYear(), eventObj.date.getMonth(), 1));
    }
    
    setShowAddModal(false);
    setConflictPendingData(null);
    setEditingEventId(null);
  };

  // 1. 编辑订单逻辑
  const handleEditEvent = (event) => {
    let mode = 'fuzzy';
    let fuzzy = '全天';
    let start = '09:00';
    let end = '12:00';

    if (event.time && event.time.includes('-')) {
      mode = 'exact';
      const parts = event.time.split('-');
      start = parts[0].trim();
      end = parts[1].trim();
    } else if (event.time) {
      fuzzy = event.time;
    }

    const y = event.date.getFullYear();
    const m = String(event.date.getMonth() + 1).padStart(2, '0');
    const d = String(event.date.getDate()).padStart(2, '0');

    setFormData({
      client: event.client || '',
      type: event.type,
      date: `${y}-${m}-${d}`,
      timeMode: mode,
      fuzzyTime: fuzzy,
      exactStart: start,
      exactEnd: end,
      location: event.location || '',
      remarks: event.remarks || ''
    });
    setEditingEventId(event.id);
    setShowDayModal(false);
    setShowAddModal(true);
  };

  // 1. 删除订单逻辑
  const handleDeleteEvent = (id) => {
    setEvents(prev => prev.filter(e => e.id !== id));
    setDeletePendingId(null); // 删除后重置确认状态
    // 删除了原本“如果订单为空则直接 setShowDayModal(false)”的强制退出逻辑，保留弹窗平滑过渡到空状态
  };

  // 4. 复制行程逻辑
  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 2500);
  };

  const copySchedule = () => {
    const sortedEvents = events
      .filter(e => isSameDate(e.date, selectedDate))
      .sort((a, b) => parseTimeToMinutes(a.time) - parseTimeToMinutes(b.time));

    let text = `📅 ${selectedDate.getFullYear()}年${selectedDate.getMonth() + 1}月${selectedDate.getDate()}日 行程安排\n\n`;
    sortedEvents.forEach((e, idx) => {
      text += `【${idx + 1}】 ${e.time} | ${e.typeLabel}\n`;
      text += `👤 客户: ${e.client}\n`;
      if (e.location) text += `📍 地点: ${e.location}\n`;
      if (e.remarks) text += `📝 备注: ${e.remarks}\n`;
      text += `\n`;
    });

    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      showToast('行程已成功复制到剪贴板 ✨');
    } catch (err) {
      showToast('复制失败，请重试');
    }
    document.body.removeChild(textArea);
  };

  // --- 日历生成逻辑 (保持原有精美样式) ---
  const getDaysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
  const getFirstDayOfMonth = (year, month) => new Date(year, month, 1).getDay();

  const generateCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    
    const days = [];
    const prevMonthDays = getDaysInMonth(year, month - 1);
    for (let i = 0; i < firstDay; i++) {
      days.push({ day: prevMonthDays - firstDay + i + 1, isCurrentMonth: false, date: new Date(year, month - 1, prevMonthDays - firstDay + i + 1) });
    }
    for (let i = 1; i <= daysInMonth; i++) {
      days.push({ day: i, isCurrentMonth: true, date: new Date(year, month, i) });
    }
    const remainingSlots = 42 - days.length;
    for (let i = 1; i <= remainingSlots; i++) {
      days.push({ day: i, isCurrentMonth: false, date: new Date(year, month + 1, i) });
    }
    return days;
  };

  const calendarDays = generateCalendar();
  const weekDays = ['日', '一', '二', '三', '四', '五', '六'];

  const isSameDate = (date1, date2) => {
    return date1.getFullYear() === date2.getFullYear() && date1.getMonth() === date2.getMonth() && date1.getDate() === date2.getDate();
  };

  const nextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  const prevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  
  const goToToday = () => {
    const today = new Date();
    setCurrentDate(today);
    setSelectedDate(today);
  };

  const isCurrentMonthView = currentDate.getFullYear() === new Date().getFullYear() && currentDate.getMonth() === new Date().getMonth();

  const getTagStyle = (type) => {
    // 所有 custom_ 开头的自定义类型统一赋予青色样式
    if (type?.startsWith('custom')) return 'bg-teal-100 text-teal-600 border border-teal-100';
    
    switch (type) {
      case 'wedding': return 'bg-pink-100 text-pink-600 border border-pink-100';     
      case 'engagement': return 'bg-rose-100 text-rose-600 border border-rose-100';    
      case 'birthday': return 'bg-yellow-100 text-yellow-600 border border-yellow-100'; 
      case 'registration': return 'bg-red-100 text-red-600 border border-red-100'; 
      case 'creative': return 'bg-purple-100 text-purple-600 border border-purple-100';     
      case 'banquet': return 'bg-blue-100 text-blue-600 border border-blue-100';     
      default: return 'bg-gray-100 text-gray-600 border border-gray-100';
    }
  };

  // 新增：智能时间解析排序函数
  const parseTimeToMinutes = (timeStr) => {
    if (!timeStr) return 9999; // 没有时间的默认排在最后
    
    // 处理模糊时间权重
    if (timeStr.includes('全天')) return -1; // 全天优先级最高，排在最前
    if (timeStr.includes('上午')) return 8 * 60; // 假设上午基准为 8:00
    if (timeStr.includes('下午')) return 13 * 60; // 假设下午基准为 13:00
    if (timeStr.includes('晚上')) return 18 * 60; // 假设晚上基准为 18:00

    // 处理精确时间，例如 "09:00 - 12:00" 取 "09:00"
    const timeMatch = timeStr.match(/(\d{2}):(\d{2})/);
    if (timeMatch) {
      const hours = parseInt(timeMatch[1], 10);
      const minutes = parseInt(timeMatch[2], 10);
      return hours * 60 + minutes;
    }
    
    return 9999;
  };

  const getLunarMock = (day) => {
    const lunars = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十', 
                    '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十'];
    const terms = { 5: '立夏', 21: '小满' }; 
    if (terms[day]) return <span className="text-green-600">{terms[day]}</span>;
    return <span className="text-gray-400">{lunars[(day - 1) % 20]}</span>;
  };

  // 优化：弹窗里的选中日期订单同样按照时间早晚排序
  const selectedDateEvents = events
    .filter(e => isSameDate(e.date, selectedDate))
    .sort((a, b) => parseTimeToMinutes(a.time) - parseTimeToMinutes(b.time));

  return (
    <div 
      className="max-w-md mx-auto bg-white h-[100dvh] w-full shadow-2xl overflow-hidden flex flex-col font-sans relative select-none"
      style={{ 
        WebkitTapHighlightColor: 'transparent',
        paddingTop: 'env(safe-area-inset-top)',
        paddingBottom: 'env(safe-area-inset-bottom)'
      }}
    >
      
      {/* 顶部导航 - 固定不滚动 */}
      <div className="flex-none flex items-center justify-between px-5 pt-12 pb-4 bg-white z-20">
        <div className="flex items-center space-x-2">
          <button onClick={prevMonth} className="p-1 hover:bg-gray-100 rounded-full transition-colors active:scale-95"><ChevronLeft size={20} className="text-gray-600" /></button>
          <h1 className="text-2xl font-bold tracking-wider text-gray-800">
            {currentDate.getFullYear()}/{(currentDate.getMonth() + 1).toString().padStart(2, '0')}
          </h1>
          <button onClick={nextMonth} className="p-1 hover:bg-gray-100 rounded-full transition-colors active:scale-95"><ChevronRight size={20} className="text-gray-600" /></button>
        </div>
        <div className="flex space-x-3 text-gray-600">
          {!isCurrentMonthView && (
            <button 
              onClick={goToToday}
              className="w-9 h-9 text-sm font-bold bg-blue-50 text-blue-600 rounded-xl hover:bg-blue-100 transition-colors flex items-center justify-center shadow-sm active:scale-95"
            >
              今
            </button>
          )}
          <button 
            onClick={() => {
              setPickerYear(currentDate.getFullYear());
              setPickerMonth(currentDate.getMonth());
              setShowDatePicker(true);
            }} 
            className="p-2 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors active:scale-95"
          >
            <CalendarIcon size={20} />
          </button>
        </div>
      </div>

      {/* 星期表头 - 固定不滚动 */}
      <div className="flex-none grid grid-cols-7 text-center pb-2 border-b border-gray-100 bg-white z-20 shadow-sm">
        {weekDays.map((day, index) => (
          <div key={index} className={`text-sm font-medium ${index === 0 || index === 6 ? 'text-red-400' : 'text-gray-500'}`}>
            {day}
          </div>
        ))}
      </div>

      {/* 日历网格 - 独立滚动区 */}
      <div className="flex-1 bg-white overflow-y-auto hide-scrollbar pb-28 overscroll-contain">
        <div className="grid grid-cols-7">
          {calendarDays.map((dayObj, index) => {
            // 优化：筛选出当天的订单，并按照时间先后排序
            const dayEvents = events
              .filter(e => isSameDate(e.date, dayObj.date))
              .sort((a, b) => parseTimeToMinutes(a.time) - parseTimeToMinutes(b.time));
              
            const isSelected = isSameDate(dayObj.date, selectedDate);
            const isToday = isSameDate(dayObj.date, new Date());
            
            return (
              <div 
                key={index} 
                onClick={() => {
                  setSelectedDate(dayObj.date);
                  // 如果点击的日期有订单，则打开中间的弹窗
                  if (dayEvents.length > 0) {
                    setShowDayModal(true);
                  }
                }}
                className={`
                  min-h-[95px] p-1 flex flex-col items-center cursor-pointer rounded-xl
                  transition-all duration-300 ease-out
                  ${isSelected ? 'bg-blue-50/40 ring-1 ring-inset ring-blue-200 shadow-sm z-10 transform scale-[1.02]' : 'hover:bg-gray-50'}
                `}
              >
                <div className="flex flex-col items-center mb-1 w-full relative pt-1.5">
                  {/* 使用绝对定位的长方形背景，彻底与文本流剥离，绝不影响下方农历的对齐和间距 */}
                  {isToday && (
                    <div className="absolute top-[3px] w-[34px] h-[22px] bg-blue-600 rounded-md shadow-sm z-0"></div>
                  )}
                  <span className={`
                    text-base font-semibold leading-none z-10
                    ${isToday ? 'text-white' : 
                      !dayObj.isCurrentMonth ? 'text-gray-300' : 
                      (dayObj.date.getDay() === 0 || dayObj.date.getDay() === 6) ? 'text-red-400' : 'text-gray-800'}
                  `}>
                    {dayObj.day}
                  </span>
                  {/* 还原回原始的紧凑间距 */}
                  <span className={`text-[10px] leading-none scale-90 opacity-80 mt-1 z-10 ${isToday ? 'text-blue-600 font-bold' : ''}`}>
                    {getLunarMock(dayObj.day)}
                  </span>
                </div>

                <div className="w-full flex flex-col space-y-[3px] px-0.5 overflow-hidden pointer-events-none">
                  {dayEvents.slice(0, 3).map((event, i) => (
                    <div 
                      key={i} 
                      className={`text-[10px] leading-tight px-1 py-[3px] rounded-md text-center truncate font-medium ${getTagStyle(event.type)}`}
                    >
                      {event.typeLabel || event.type}
                    </div>
                  ))}
                  {dayEvents.length > 3 && (
                    <div className="text-[10px] text-gray-400 text-center font-bold scale-75 mt-0.5">
                      • • •
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 每日订单详情弹窗 (居中毛玻璃效果) */}
      {showDayModal && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-5">
          {/* 毛玻璃背景遮罩 */}
          <div 
            className="absolute inset-0 bg-black/20 backdrop-blur-md transition-opacity"
            onClick={() => setShowDayModal(false)}
          ></div>
          
          {/* 弹窗主体 */}
          <div className="relative bg-white/75 backdrop-blur-2xl border border-white/50 rounded-3xl w-full max-w-sm shadow-2xl flex flex-col max-h-[80vh] animate-pop-in">
            <div className="p-5 pb-4 flex justify-between items-center border-b border-gray-200/40">
              <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                {selectedDate.getMonth() + 1}月{selectedDate.getDate()}日 
                <span className="text-sm font-normal text-gray-600 px-2 py-0.5 bg-white/60 rounded-full shadow-sm">
                  {selectedDateEvents.length} 单
                </span>
              </h3>
              <div className="flex items-center gap-2">
                {selectedDateEvents.length > 0 && (
                  <button 
                    onClick={copySchedule} 
                    className="p-1.5 bg-white/50 hover:bg-white rounded-full text-blue-600 shadow-sm transition-colors"
                    title="一键复制行程"
                  >
                    <Copy size={16} />
                  </button>
                )}
                <button 
                  onClick={() => setShowDayModal(false)} 
                  className="p-1.5 bg-white/50 hover:bg-white rounded-full text-gray-600 shadow-sm transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
            </div>
            
            <div className="p-5 space-y-4 overflow-y-auto hide-scrollbar">
              {/* 订单列表 或 空状态缺省页 */}
              {selectedDateEvents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 opacity-80 animate-pop-in">
                  <div className="w-16 h-16 bg-gray-100/80 rounded-full flex items-center justify-center mb-4">
                    <CalendarIcon size={28} className="text-gray-400" />
                  </div>
                  <p className="text-sm font-medium text-gray-500 mb-1">今日暂无档期</p>
                  <p className="text-xs text-gray-400">可以点击下方按钮添加新安排</p>
                </div>
              ) : (
                selectedDateEvents.map((event, idx) => (
                    <div key={idx} className="bg-white/80 backdrop-blur-sm rounded-2xl p-4 flex gap-4 border border-white shadow-sm hover:shadow-md transition-all relative group">
                      <div className={`w-1.5 rounded-full ${getTagStyle(event.type).split(' ')[0]}`}></div>
                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-2 pr-16">
                          <h4 className="font-bold text-gray-800 text-base">{event.title}</h4>
                          <span className={`text-xs px-2 py-1 rounded-full ${getTagStyle(event.type)}`}>
                            {event.typeLabel || event.type}
                          </span>
                        </div>

                        {/* 1. 编辑和删除操作区 (绝对定位在卡片右上角) */}
                        <div className="absolute top-3.5 right-3.5 flex items-center gap-1.5">
                          <button onClick={() => handleEditEvent(event)} className="p-1.5 bg-white hover:bg-blue-50 text-gray-400 hover:text-blue-500 rounded-lg shadow-sm border border-gray-100 transition-colors">
                            <Edit3 size={14} />
                          </button>
                          <button onClick={() => setDeletePendingId(event.id)} className="p-1.5 bg-white hover:bg-red-50 text-gray-400 hover:text-red-500 rounded-lg shadow-sm border border-gray-100 transition-colors">
                            <Trash2 size={14} />
                          </button>
                        </div>

                        {event.time && (
                          <div className="flex items-center text-gray-600 text-xs mt-1.5 font-medium">
                            <Clock size={13} className="mr-1.5 opacity-70" /> {event.time}
                          </div>
                        )}
                        {event.location && (
                          <div className="flex items-center text-gray-600 text-xs mt-1.5 font-medium">
                            <MapPin size={13} className="mr-1.5 opacity-70" /> {event.location}
                          </div>
                        )}
                        {event.client && (
                          <div className="text-xs text-gray-700 mt-3 bg-white/60 px-3 py-1.5 rounded-lg border border-white/50 flex items-center shadow-sm">
                            <span className="font-semibold">{event.client}</span> 
                            <span className="mx-2 text-gray-400">|</span> 
                            <span className="text-blue-600 font-medium">{event.phone || '暂无电话'}</span>
                          </div>
                        )}
                        {event.remarks && (
                          <div className="text-xs text-gray-600 mt-2 bg-white/50 px-3 py-2 rounded-lg border border-white/50 shadow-sm whitespace-pre-wrap">
                            <span className="font-semibold text-gray-700">备注：</span>{event.remarks}
                          </div>
                        )}
                      </div>
                    </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 右下角悬浮添加按钮 */}
      <button 
        onClick={() => {
          setFormData({ 
            client: '', type: 'wedding', date: '', 
            timeMode: 'fuzzy', fuzzyTime: '全天', exactStart: '09:00', exactEnd: '12:00', 
            location: '', remarks: '' 
          });
          setIsAddingCustom(false);
          setTempCustomType('');
          setIsEditingTypes(false); 
          setEditingEventId(null); // 清除编辑状态
          setShowAddModal(true);
        }}
        className="absolute right-6 bottom-8 w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-full shadow-xl shadow-blue-200 flex items-center justify-center hover:scale-105 active:scale-95 transition-all z-20"
      >
        <Plus size={28} strokeWidth={2.5} />
      </button>

      {/* 新建档期弹窗 */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 transition-opacity" style={{ paddingTop: 'env(safe-area-inset-top)' }}>
          <div className="bg-white rounded-3xl w-full max-w-sm overflow-hidden shadow-2xl transform transition-all flex flex-col animate-pop-in">
            <div className="p-5 pb-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
              <h2 className="text-lg font-bold text-gray-800">{editingEventId ? '编辑档期' : '新建档期'}</h2>
              <button onClick={() => { setShowAddModal(false); setEditingEventId(null); }} className="p-1.5 bg-white hover:bg-gray-100 shadow-sm rounded-full text-gray-500 transition-colors">
                <X size={18} />
              </button>
            </div>
            
            <div className="p-5 space-y-4 overflow-y-auto max-h-[65vh] hide-scrollbar">
              {/* 客户姓名 */}
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">客户姓名</label>
                <input 
                  type="text" 
                  value={formData.client} 
                  onChange={e => setFormData({...formData, client: e.target.value})} 
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all" 
                  placeholder="例如：张女士" 
                />
              </div>
              
              {/* 订单类型 */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-xs font-semibold text-gray-700">订单类型</label>
                  <button 
                    onClick={() => {
                      setIsEditingTypes(!isEditingTypes);
                      setIsAddingCustom(false); // 优化：点击管理时，如果有正在输入的自定义框，自动收起它
                    }}
                    className={`text-[11px] font-bold px-2 py-0.5 rounded-md transition-colors ${isEditingTypes ? 'text-blue-600 bg-blue-50' : 'text-gray-400 hover:text-gray-600 bg-gray-50 hover:bg-gray-100'}`}
                  >
                    {isEditingTypes ? '完成' : '管理'}
                  </button>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {dynamicEventTypes.map(t => (
                    <div key={t.id} className={`relative ${isEditingTypes ? 'animate-wiggle' : ''}`}>
                      <button
                        onClick={() => {
                          if (!isEditingTypes) setFormData({...formData, type: t.id});
                        }}
                        className={`w-full py-2 rounded-lg text-xs font-medium transition-all ${formData.type === t.id && !isEditingTypes ? 'bg-blue-100 text-blue-600 ring-1 ring-blue-300' : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-100'} ${isEditingTypes ? 'opacity-70 pointer-events-none' : ''}`}
                      >
                        {t.label}
                      </button>
                      
                      {/* 红色删除小叉 (仅在编辑模式下显示) */}
                      {isEditingTypes && (
                        <button
                          onClick={(e) => handleDeleteType(e, t.id)}
                          className="absolute -top-1.5 -right-1.5 w-[18px] h-[18px] bg-red-500 text-white rounded-full flex items-center justify-center shadow-sm border border-white z-10 hover:bg-red-600 active:scale-90 transition-transform"
                        >
                          <X size={11} strokeWidth={3} />
                        </button>
                      )}
                    </div>
                  ))}
                  
                  {/* 原地切换的自定义按钮 (非编辑模式才显示) */}
                  {!isEditingTypes && (
                    isAddingCustom ? (
                      <div className="flex items-center gap-1 col-span-1 border border-blue-300 bg-blue-50 rounded-lg px-2 ring-1 ring-blue-300 transition-all">
                        <input 
                          autoFocus
                          type="text"
                          maxLength={5}
                          value={tempCustomType}
                          onChange={e => setTempCustomType(e.target.value)}
                          onKeyDown={e => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              handleConfirmCustom();
                            }
                          }}
                          onBlur={handleConfirmCustom}
                          className="w-full bg-transparent text-xs text-blue-700 focus:outline-none text-center font-medium"
                          placeholder="输入.."
                        />
                      </div>
                    ) : (
                      <button
                        onClick={() => setIsAddingCustom(true)}
                        className="py-2 rounded-lg text-xs font-medium bg-gray-50 text-gray-500 hover:bg-gray-100 border border-gray-200 border-dashed transition-all"
                      >
                        + 自定义
                      </button>
                    )
                  )}
                </div>
              </div>

              {/* 日期 (单独占一行) */}
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">日期</label>
                <input 
                  type="date" 
                  value={formData.date} 
                  onChange={e => setFormData({...formData, date: e.target.value})} 
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all" 
                />
              </div>

              {/* 时间 (拆分后单独一行，带多模式切换) */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-xs font-semibold text-gray-700">时间</label>
                  {/* iOS风格分段控制器 */}
                  <div className="flex bg-gray-200/60 p-0.5 rounded-lg">
                    <button
                      onClick={() => setFormData({...formData, timeMode: 'fuzzy'})}
                      className={`px-3 py-1 text-[10px] font-bold rounded-md transition-all ${formData.timeMode === 'fuzzy' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'}`}
                    >
                      模糊
                    </button>
                    <button
                      onClick={() => setFormData({...formData, timeMode: 'exact'})}
                      className={`px-3 py-1 text-[10px] font-bold rounded-md transition-all ${formData.timeMode === 'exact' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'}`}
                    >
                      精确
                    </button>
                  </div>
                </div>

                {formData.timeMode === 'fuzzy' ? (
                  /* 模糊时间标签池 */
                  <div className="grid grid-cols-4 gap-2">
                    {['全天', '上午', '下午', '晚上'].map(t => (
                      <button
                        key={t}
                        onClick={() => setFormData({...formData, fuzzyTime: t})}
                        className={`py-2.5 rounded-xl text-xs font-medium transition-all ${formData.fuzzyTime === t ? 'bg-blue-100 text-blue-600 ring-1 ring-blue-300' : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-100'}`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                ) : (
                  /* 精确时间段选择器 */
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <select
                        value={formData.exactStart}
                        onChange={e => {
                           const newStart = e.target.value;
                           let newEnd = formData.exactEnd;
                           // 防错：如果新开始时间 晚于或等于 结束时间，自动将结束时间往后推1小时（2个选项）
                           if (timeOptions.indexOf(newEnd) <= timeOptions.indexOf(newStart)) {
                             const nextIdx = Math.min(timeOptions.indexOf(newStart) + 2, timeOptions.length - 1);
                             newEnd = timeOptions[nextIdx];
                           }
                           setFormData({...formData, exactStart: newStart, exactEnd: newEnd});
                        }}
                        className="w-full pl-4 pr-8 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white appearance-none"
                      >
                        {timeOptions.map(t => <option key={`start-${t}`} value={t}>{t}</option>)}
                      </select>
                      <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                    </div>
                    <span className="text-gray-400 text-xs font-medium px-1">至</span>
                    <div className="relative flex-1">
                      <select
                        value={formData.exactEnd}
                        onChange={e => {
                           const newEnd = e.target.value;
                           let newStart = formData.exactStart;
                           // 防错：如果新结束时间 早于或等于 开始时间，自动将开始时间往前推1小时
                           if (timeOptions.indexOf(newEnd) <= timeOptions.indexOf(newStart)) {
                             const prevIdx = Math.max(timeOptions.indexOf(newEnd) - 2, 0);
                             newStart = timeOptions[prevIdx];
                           }
                           setFormData({...formData, exactStart: newStart, exactEnd: newEnd});
                        }}
                        className="w-full pl-4 pr-8 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white appearance-none"
                      >
                        {timeOptions.map(t => <option key={`end-${t}`} value={t}>{t}</option>)}
                      </select>
                      <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                    </div>
                  </div>
                )}
              </div>

              {/* 地点 */}
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">地点</label>
                <input 
                  type="text" 
                  value={formData.location} 
                  onChange={e => setFormData({...formData, location: e.target.value})} 
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all" 
                  placeholder="例如：东湖公园" 
                />
              </div>

              {/* 备注 */}
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">备注</label>
                <textarea 
                  value={formData.remarks} 
                  onChange={e => setFormData({...formData, remarks: e.target.value})} 
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all resize-none h-20" 
                  placeholder="例如：客户要求多拍侧脸、需带航拍器等..." 
                />
              </div>
            </div>

            <div className="p-5 pt-3 border-t border-gray-50">
              <button 
                onClick={handleSaveEvent}
                disabled={!formData.client || !formData.date}
                className="w-full py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md shadow-blue-200"
              >
                {editingEventId ? '保存修改' : '保存档期'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. 冲突防错提示弹窗 */}
      {conflictPendingData && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-center justify-center p-5 transition-opacity">
          <div className="bg-white rounded-3xl w-full max-w-[320px] overflow-hidden shadow-2xl transform transition-all flex flex-col animate-pop-in p-6">
            <div className="flex items-center gap-3 text-red-500 mb-3">
              <AlertCircle size={24} />
              <h3 className="text-lg font-bold text-gray-800">档期冲突提醒</h3>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed mb-6">
              {conflictPendingData.warningMsg}
              <br/><span className="text-gray-400 text-xs mt-1 block">仍要强制保存吗？</span>
            </p>
            <div className="flex gap-3">
              <button 
                onClick={() => setConflictPendingData(null)}
                className="flex-1 py-2.5 bg-gray-100 text-gray-700 rounded-xl font-bold hover:bg-gray-200 transition-colors"
              >
                取消
              </button>
              <button 
                onClick={() => executeSave(conflictPendingData.newEvent)}
                className="flex-1 py-2.5 bg-red-500 text-white rounded-xl font-bold hover:bg-red-600 shadow-md shadow-red-200 transition-colors"
              >
                强制保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4. 全局 Toast 提示 */}
      {toastMsg && (
        <div className="fixed top-[15%] left-1/2 -translate-x-1/2 z-[70] bg-gray-800/90 backdrop-blur text-white px-5 py-3 rounded-full shadow-xl flex items-center gap-2 text-sm font-medium animate-slide-down">
          <CheckCircle2 size={16} className="text-green-400" />
          {toastMsg}
        </div>
      )}

      {/* 5. 删除确认弹窗 */}
      {deletePendingId && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-center justify-center p-5 transition-opacity">
          <div className="bg-white rounded-3xl w-full max-w-[300px] overflow-hidden shadow-2xl transform transition-all flex flex-col animate-pop-in p-6">
            <div className="flex items-center gap-3 text-red-500 mb-3">
              <Trash2 size={24} />
              <h3 className="text-lg font-bold text-gray-800">删除档期</h3>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed mb-6">
              确定要删除这条档期安排吗？<br/>删除后将无法恢复。
            </p>
            <div className="flex gap-3">
              <button 
                onClick={() => setDeletePendingId(null)}
                className="flex-1 py-2.5 bg-gray-100 text-gray-700 rounded-xl font-bold hover:bg-gray-200 transition-colors"
              >
                取消
              </button>
              <button 
                onClick={() => handleDeleteEvent(deletePendingId)}
                className="flex-1 py-2.5 bg-red-500 text-white rounded-xl font-bold hover:bg-red-600 shadow-md shadow-red-200 transition-colors"
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* iOS风格年月选择器弹窗 */}
      {showDatePicker && (
        <div className="fixed inset-0 z-50 flex flex-col justify-end">
          <div 
            className="absolute inset-0 bg-black/30 backdrop-blur-sm transition-opacity" 
            onClick={() => setShowDatePicker(false)}
          ></div>
          <div className="relative bg-white rounded-t-3xl shadow-[0_-10px_40px_rgba(0,0,0,0.1)] animate-slide-up pb-8 pt-2">
            {/* 顶部小横条提示 */}
            <div className="w-12 h-1.5 bg-gray-200 rounded-full mx-auto mb-2"></div>
            
            <div className="flex justify-between items-center p-4 border-b border-gray-100">
              <button onClick={() => setShowDatePicker(false)} className="text-gray-500 font-medium px-2 py-1 hover:bg-gray-50 rounded-lg">取消</button>
              <h3 className="text-[17px] font-bold text-gray-800">选择年月</h3>
              <button onClick={handleConfirmDate} className="text-blue-600 font-bold px-2 py-1 hover:bg-blue-50 rounded-lg">确定</button>
            </div>
            
            <div className="flex px-4 py-4 space-x-2">
              <ScrollPicker items={years} value={pickerYear} onChange={setPickerYear} label="年" />
              <ScrollPicker items={months} value={pickerMonth} onChange={setPickerMonth} label="月" />
            </div>
          </div>
        </div>
      )}

      <style dangerouslySetInnerHTML={{__html: `
        /* 禁止整个页面的橡皮筋效果，只允许内部元素滚动 */
        body {
          overscroll-behavior-y: none;
          background-color: #f3f4f6; /* 在PC上预览时的背景色 */
        }
        
        .hide-scrollbar::-webkit-scrollbar { display: none; }
        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        
        @keyframes popIn {
          0% { opacity: 0; transform: scale(0.95) translateY(10px); }
          100% { opacity: 1; transform: scale(1) translateY(0); }
        }
        .animate-pop-in {
          animation: popIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        .animate-slide-up {
          animation: slideUp 0.35s cubic-bezier(0.32, 0.72, 0, 1) forwards;
        }

        .picker-mask {
          -webkit-mask-image: linear-gradient(to bottom, transparent, black 35%, black 65%, transparent);
          mask-image: linear-gradient(to bottom, transparent, black 35%, black 65%, transparent);
        }

        /* iOS 抖动删除动效 */
        @keyframes wiggle {
          0%, 100% { transform: rotate(-1.5deg); }
          50% { transform: rotate(1.5deg); }
        }
        .animate-wiggle {
          animation: wiggle 0.25s ease-in-out infinite;
        }

        @keyframes slideDown {
          from { transform: translate(-50%, -20px); opacity: 0; }
          to { transform: translate(-50%, 0); opacity: 1; }
        }
        .animate-slide-down {
          animation: slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}} />
    </div>
  );
};

export default PhotographerCalendarApp;